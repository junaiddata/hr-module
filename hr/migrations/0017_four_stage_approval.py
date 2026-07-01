from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0016_department_choices'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Replace Admin/Employee choices with Manager/MD/HR
        migrations.AlterField(
            model_name='role',
            name='role',
            field=models.CharField(
                choices=[
                    ('Head', 'Head'),
                    ('Manager', 'Manager'),
                    ('MD', 'MD'),
                    ('HR', 'HR'),
                ],
                max_length=20,
            ),
        ),
        # Expand Leave.status to hold longer values and add new statuses
        migrations.AlterField(
            model_name='leave',
            name='status',
            field=models.CharField(
                choices=[
                    ('Pending', 'Pending'),
                    ('Head_Approved', 'Head Approved'),
                    ('Manager_Approved', 'Manager Approved'),
                    ('MD_Approved', 'MD Approved'),
                    ('Approved', 'Approved'),
                    ('Rejected', 'Rejected'),
                ],
                default='Pending',
                max_length=20,
            ),
        ),
        # Stage 2: Manager approval fields
        migrations.AddField(
            model_name='leave',
            name='manager_approved_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='manager_approved_leaves',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='leave',
            name='manager_approved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        # Stage 3: MD approval fields
        migrations.AddField(
            model_name='leave',
            name='md_approved_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='md_approved_leaves',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='leave',
            name='md_approved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
