"""Refresh document-expiry Notification rows (visa/EID/labour card/insurance/
driving license, MOL trade license/tenancy/establishment card, vehicle
mulkiya, management-member documents) plus the weekly labour-camp-contract
renewal reminders — without waiting for someone to open /notifications/.

This reuses the exact same generation logic the notifications page runs on
every visit (hr.views._generate_expiry_notifications /
_generate_labour_camp_renewal_notifications), so results are identical either
way — this just means alerts (and, for labour camp agreements, the weekly
repeat) get created on a schedule instead of only when HR happens to load
that page.

Run daily (Windows Task Scheduler / cron):
    python manage.py generate_expiry_notifications
"""
import logging

from django.core.management.base import BaseCommand

from hr.models import Notification
from hr.views import (
    _cleanup_old_read_notifications,
    _dedupe_read_notifications,
    _generate_expiry_notifications,
    _generate_labour_camp_renewal_notifications,
)

logger = logging.getLogger('hr.notifications')


class Command(BaseCommand):
    help = "Refresh document-expiry and labour-camp-renewal notifications."

    def handle(self, *args, **opts):
        before = Notification.objects.filter(is_read=False).count()

        _generate_expiry_notifications()
        _generate_labour_camp_renewal_notifications()
        _dedupe_read_notifications()
        _cleanup_old_read_notifications()

        after = Notification.objects.filter(is_read=False).count()
        msg = f'Notification refresh done. Unread: {before} -> {after}.'
        self.stdout.write(self.style.SUCCESS(msg))
        logger.info(msg)
