# management/commands/generate_notifications.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from hr.models import Employee, Notification
from datetime import timedelta

class Command(BaseCommand):
    help = 'Generate birthday and document expiry notifications'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        upcoming = today + timedelta(days=7)

        # Birthday Wishes
        birthdays = Employee.objects.filter(dob__month=today.month, dob__day=today.day)
        for emp in birthdays:
            Notification.objects.create(
                title="🎉 Birthday Alert",
                message=f"Today is {emp.emp_name}'s birthday!",
                employee=emp
            )

        # Document Expiry Alerts
        expiry_fields = [
            ('visa_expiry', 'Visa'),
            ('passport_expiry', 'Passport'),
            ('labour_card_expiry', 'Labour Card'),
            ('eid_expiry', 'EID'),
        ]
        for field, doc_name in expiry_fields:
            filter_kwargs = {f"{field}__range": [today, upcoming]}
            expiring_emps = Employee.objects.filter(**filter_kwargs)
            for emp in expiring_emps:
                expiry_date = getattr(emp, field)
                Notification.objects.create(
                    title="📄 Document Expiry Soon",
                    message=f"{emp.emp_name}'s {doc_name} is expiring on {expiry_date}",
                    employee=emp
                )
