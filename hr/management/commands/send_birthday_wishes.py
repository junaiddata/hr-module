"""Send WhatsApp birthday wishes to employees whose birthday is today.

Run daily (Windows Task Scheduler / cron):
    python manage.py send_birthday_wishes

Options:
    --force     Resend even if a wish was already sent this year.
    --dry-run   Show who would be wished without sending anything.
"""
import logging
from datetime import date

from django.core.management.base import BaseCommand

from hr.models import Employee, BirthdayWish
from hr.whatsapp import send_birthday_wish, whatsapp_configured

logger = logging.getLogger('hr.birthday')


class Command(BaseCommand):
    help = "Send WhatsApp birthday wishes to employees whose birthday is today."

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Resend even if a wish was already sent this year.')
        parser.add_argument('--dry-run', action='store_true',
                            help='List who would receive a wish without sending.')

    def handle(self, *args, **opts):
        today = date.today()
        year = today.year
        dry = opts['dry_run']

        if not dry and not whatsapp_configured():
            msg = ('WhatsApp API is not configured. Set WHATSAPP_ACCESS_TOKEN '
                   'and WHATSAPP_PHONE_NUMBER_ID before running for real.')
            self.stderr.write(self.style.ERROR(msg))
            logger.error('Run aborted: %s', msg)
            return

        emps = Employee.objects.filter(
            is_active=True, dob__month=today.month, dob__day=today.day
        ).order_by('emp_name')

        if not emps:
            self.stdout.write('No birthdays today.')
            logger.info('Run start%s: no birthdays today.', ' (dry-run)' if dry else '')
            return

        logger.info('Run start%s: %d birthday(s) today.',
                    ' (dry-run)' if dry else '', emps.count())

        sent = skipped = failed = 0
        for emp in emps:
            already = BirthdayWish.objects.filter(
                employee=emp, year=year, status='sent').exists()
            if already and not opts['force']:
                skipped += 1
                self.stdout.write(f'  skip   {emp.emp_name} (already wished this year)')
                logger.info('SKIP   %s (already wished this year)', emp.emp_name)
                continue

            if dry:
                self.stdout.write(f'  would  {emp.emp_name} -> {emp.contact_number}')
                logger.info('WOULD  %s -> %s', emp.emp_name, emp.contact_number)
                continue

            # send_birthday_wish() already logs the per-employee SENT/FAILED line
            ok, info = send_birthday_wish(emp)
            if ok:
                sent += 1
                self.stdout.write(self.style.SUCCESS(f'  sent   {emp.emp_name} ({info})'))
            else:
                failed += 1
                self.stdout.write(self.style.ERROR(f'  fail   {emp.emp_name}: {info}'))

        summary = f'sent={sent} skipped={skipped} failed={failed}'
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING(f'Done. {summary}'))
        logger.info('Run done%s: %s', ' (dry-run)' if dry else '', summary)
