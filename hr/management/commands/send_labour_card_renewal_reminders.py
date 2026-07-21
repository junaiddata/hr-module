"""Send WhatsApp 'do you want to renew your visa?' prompts to employees whose
labour card is within N days of expiry (default 60 — about 2 months).

Run daily (Windows Task Scheduler / cron):
    python manage.py send_labour_card_renewal_reminders

Options:
    --days N    Days-before-expiry window to trigger on (default 60).
    --force     Resend even if a prompt was already sent for this expiry date.
    --dry-run   Show who would be prompted without sending anything.
"""
import logging
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from hr.models import Employee, LabourCardRenewalPrompt, Notification
from hr.whatsapp import send_labour_card_renewal_prompt, whatsapp_configured

logger = logging.getLogger('hr.labour_card_renewal')


class Command(BaseCommand):
    help = "Send WhatsApp labour-card renewal prompts to employees within N days of expiry."

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=60,
                            help='Days-before-expiry window to trigger on (default 60).')
        parser.add_argument('--force', action='store_true',
                            help='Resend even if a prompt was already sent for this expiry date.')
        parser.add_argument('--dry-run', action='store_true',
                            help='List who would be prompted without sending anything.')

    def handle(self, *args, **opts):
        today = date.today()
        window = opts['days']
        dry = opts['dry_run']
        cutoff = today + timedelta(days=window)

        if not dry and not whatsapp_configured():
            msg = ('WhatsApp API is not configured. Set WHATSAPP_ACCESS_TOKEN '
                   'and WHATSAPP_PHONE_NUMBER_ID before running for real.')
            self.stderr.write(self.style.ERROR(msg))
            logger.error('Labour renewal run aborted: %s', msg)
            return

        emps = Employee.objects.filter(
            is_active=True,
            labour_card_expiry__isnull=False,
            labour_card_expiry__gte=today,
            labour_card_expiry__lte=cutoff,
        ).select_related('department').order_by('labour_card_expiry')

        if not emps:
            self.stdout.write(f'No labour cards expiring within {window} days.')
            logger.info('Labour renewal run%s: nothing due within %d days.',
                        ' (dry-run)' if dry else '', window)
            return

        logger.info('Labour renewal run%s: %d employee(s) within %d days.',
                    ' (dry-run)' if dry else '', emps.count(), window)

        sent = skipped = failed = 0
        for emp in emps:
            already = LabourCardRenewalPrompt.objects.filter(
                employee=emp, expiry_snapshot=emp.labour_card_expiry, whatsapp_status='sent',
            ).exists()
            if already and not opts['force']:
                skipped += 1
                self.stdout.write(f'  skip   {emp.emp_name} (already prompted for this expiry)')
                logger.info('SKIP   %s (already prompted for %s)', emp.emp_name, emp.labour_card_expiry)
                continue

            if dry:
                self.stdout.write(f'  would  {emp.emp_name} -> {emp.contact_number} (expires {emp.labour_card_expiry})')
                logger.info('WOULD  %s -> %s (expires %s)', emp.emp_name, emp.contact_number, emp.labour_card_expiry)
                continue

            ok, info, _prompt = send_labour_card_renewal_prompt(emp, emp.labour_card_expiry)

            if ok:
                sent += 1
                Notification.objects.create(
                    employee=emp,
                    title=f"Labour card renewal notification sent — {emp.emp_name}",
                    message=(
                        f"WhatsApp message asking whether to renew was sent to {emp.emp_name} "
                        f"(labour card expires {emp.labour_card_expiry.strftime('%d %b %Y')})."
                    ),
                    category='labour_card_renewal', doc_type='LABOUR_CARD_RENEWAL',
                    urgency='warning',
                )
                self.stdout.write(self.style.SUCCESS(f'  sent   {emp.emp_name} ({info})'))
            else:
                # Don't raise a notification for send failures — the employee's
                # existing document-expiry alert (from _generate_expiry_notifications)
                # already surfaces that their labour card is expiring; the WhatsApp
                # delivery failure itself is an ops/config issue, not something HR
                # needs an actionable notification for. It's still fully logged.
                failed += 1
                self.stdout.write(self.style.ERROR(f'  fail   {emp.emp_name}: {info}'))
                logger.error('FAILED %s: %s', emp.emp_name, info)

        summary = f'sent={sent} skipped={skipped} failed={failed}'
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING(f'Done. {summary}'))
        logger.info('Labour renewal run done%s: %s', ' (dry-run)' if dry else '', summary)
