from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0014_leave_leave_application'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Remove unique constraint from Role.role to allow multiple heads (one per department)
        migrations.AlterField(
            model_name='role',
            name='role',
            field=models.CharField(
                choices=[('Admin', 'Admin'), ('Head', 'Head'), ('Employee', 'Employee')],
                max_length=20,
            ),
        ),
        # Add department field to Role (used for Head users)
        migrations.AddField(
            model_name='role',
            name='department',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        # Add head_approved_by to Leave
        migrations.AddField(
            model_name='leave',
            name='head_approved_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='head_approved_leaves',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # Add head_approved_at to Leave
        migrations.AddField(
            model_name='leave',
            name='head_approved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        # Add rejection_reason to Leave
        migrations.AddField(
            model_name='leave',
            name='rejection_reason',
            field=models.TextField(blank=True, null=True),
        ),
    ]
