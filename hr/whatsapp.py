"""WhatsApp Cloud API (Meta) helpers — used for birthday wishes.

Credentials/template live in settings (read from env). No third-party deps:
we talk to the Graph API with the standard library so nothing extra needs to
be installed on the server.
"""
import json
import logging
import re
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger('hr.birthday')


def whatsapp_configured():
    """True once the Meta token + phone number id are set."""
    return bool(
        getattr(settings, 'WHATSAPP_ACCESS_TOKEN', '')
        and getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '')
    )


def normalize_phone(raw, default_cc=None):
    """Turn a stored contact number into WhatsApp-ready international digits.

    Handles the formats seen in this data set:
      +971 50 123 4567 / 00971...   -> 971501234567
      0501234567 (local, trunk 0)   -> 971501234567
      501234567 / 541234567 (bare)  -> 971501234567
      already 971501234567          -> unchanged
    Returns a digits-only string, or None if nothing usable is left.
    """
    if not raw:
        return None
    cc = (default_cc or getattr(settings, 'WHATSAPP_DEFAULT_COUNTRY_CODE', '971')).lstrip('+')
    digits = re.sub(r'\D', '', str(raw))
    if not digits:
        return None
    if digits.startswith('00'):          # 00-prefixed international dialling
        digits = digits[2:]
    if digits.startswith(cc):            # already carries the country code
        return digits
    if digits.startswith('0'):           # local number with a trunk 0
        return cc + digits[1:]
    return cc + digits                   # bare local subscriber number


def send_whatsapp_template(to_number, template_name, lang_code, body_params=None):
    """POST a template message via the Meta Cloud API.

    Returns (ok: bool, message_id_or_error: str).
    """
    token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', '')
    phone_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '')
    version = getattr(settings, 'WHATSAPP_API_VERSION', 'v21.0')
    if not (token and phone_id):
        return False, 'WhatsApp API not configured (missing token or phone number id).'
    if not to_number:
        return False, 'No valid recipient number.'

    template = {'name': template_name, 'language': {'code': lang_code}}
    if body_params:
        template['components'] = [{
            'type': 'body',
            'parameters': [{'type': 'text', 'text': str(p)} for p in body_params],
        }]
    payload = {
        'messaging_product': 'whatsapp',
        'to': to_number,
        'type': 'template',
        'template': template,
    }

    url = f'https://graph.facebook.com/{version}/{phone_id}/messages'
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), method='POST')
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode('utf-8'))
        msg_id = (body.get('messages') or [{}])[0].get('id', '')
        return True, msg_id or 'sent'
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode('utf-8'))
            msg = err.get('error', {}).get('message', f'HTTP {e.code}')
        except Exception:
            msg = f'HTTP {e.code}'
        return False, msg
    except Exception as e:                # network / timeout / DNS etc.
        return False, str(e)


def send_whatsapp_text(to_number, body):
    """POST a free-form text message via the Meta Cloud API.

    Only deliverable within the 24h customer-service window after the
    recipient last messaged us (used here for the renewal-response
    acknowledgement, sent right after they reply). Returns (ok, info).
    """
    token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', '')
    phone_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '')
    version = getattr(settings, 'WHATSAPP_API_VERSION', 'v21.0')
    if not (token and phone_id):
        return False, 'WhatsApp API not configured (missing token or phone number id).'
    if not to_number:
        return False, 'No valid recipient number.'

    payload = {
        'messaging_product': 'whatsapp',
        'to': to_number,
        'type': 'text',
        'text': {'body': body},
    }
    url = f'https://graph.facebook.com/{version}/{phone_id}/messages'
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), method='POST')
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            resp_body = json.loads(resp.read().decode('utf-8'))
        msg_id = (resp_body.get('messages') or [{}])[0].get('id', '')
        return True, msg_id or 'sent'
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode('utf-8'))
            msg = err.get('error', {}).get('message', f'HTTP {e.code}')
        except Exception:
            msg = f'HTTP {e.code}'
        return False, msg
    except Exception as e:                # network / timeout / DNS etc.
        return False, str(e)


def send_labour_card_renewal_prompt(employee, expiry):
    """Send the 'do you want to renew your visa?' template ~2 months before
    labour card expiry, and log a LabourCardRenewalPrompt row (one per
    employee per expiry date, so re-runs of the daily job are idempotent).

    Returns (ok: bool, info: str, prompt: LabourCardRenewalPrompt).
    """
    from .models import LabourCardRenewalPrompt

    to = normalize_phone(getattr(employee, 'contact_number', None))
    template = getattr(settings, 'WHATSAPP_LABOUR_RENEWAL_TEMPLATE', 'labour_card_renewal')
    lang = getattr(settings, 'WHATSAPP_LABOUR_RENEWAL_TEMPLATE_LANG', 'en')

    first_name = 'there'
    if employee.emp_name:
        first_name = employee.emp_name.strip().split(' ')[0] or 'there'
    params = [first_name, expiry.strftime('%d %b %Y')]

    if not to:
        ok, info = False, 'No valid contact number on file.'
    else:
        ok, info = send_whatsapp_template(to, template, lang, body_params=params)

    prompt, _created = LabourCardRenewalPrompt.objects.update_or_create(
        employee=employee, expiry_snapshot=expiry,
        defaults={
            'whatsapp_status':     'sent' if ok else 'failed',
            'whatsapp_to_number':  to or (employee.contact_number or ''),
            'whatsapp_message_id': info if ok else '',
            'whatsapp_error':      '' if ok else info,
            'whatsapp_sent_at':    _now(),
        },
    )

    who = 'auto'
    if ok:
        logger.info('LABOUR RENEWAL SENT   %s (id=%s) -> %s [%s]',
                    employee.emp_name, info, to or '?', who)
    else:
        logger.warning('LABOUR RENEWAL FAILED %s -> %s [%s]: %s',
                       employee.emp_name, to or '?', who, info)
    return ok, info, prompt


def _now():
    from django.utils import timezone
    return timezone.now()


def send_birthday_wish(employee, sent_by=None):
    """Send the configured birthday template to one employee and log the result.

    Returns (ok: bool, info: str). Always records a BirthdayWish row (sent or
    failed) so the job is idempotent and HR can see what happened.
    """
    from datetime import date
    from .models import BirthdayWish

    to = normalize_phone(getattr(employee, 'contact_number', None))
    template = getattr(settings, 'WHATSAPP_BIRTHDAY_TEMPLATE', 'birthday_wish')
    lang = getattr(settings, 'WHATSAPP_BIRTHDAY_TEMPLATE_LANG', 'en')
    use_name = getattr(settings, 'WHATSAPP_BIRTHDAY_NAME_PARAM', True)

    first_name = 'there'
    if employee.emp_name:
        first_name = employee.emp_name.strip().split(' ')[0] or 'there'
    params = [first_name] if use_name else None

    if not to:
        ok, info = False, 'No valid contact number on file.'
    else:
        ok, info = send_whatsapp_template(to, template, lang, body_params=params)

    BirthdayWish.objects.update_or_create(
        employee=employee, year=date.today().year,
        defaults={
            'status': 'sent' if ok else 'failed',
            'to_number': to or (employee.contact_number or ''),
            'message_id': info if ok else '',
            'error': '' if ok else info,
            'sent_by': sent_by,
        },
    )

    who = 'auto' if sent_by is None else getattr(sent_by, 'username', 'user')
    if ok:
        logger.info('SENT   %s (id=%s) -> %s [%s]',
                    employee.emp_name, info, to or '?', who)
    else:
        logger.warning('FAILED %s -> %s [%s]: %s',
                       employee.emp_name, to or '?', who, info)
    return ok, info
