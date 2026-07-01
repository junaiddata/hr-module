from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0024_payroll_phase1'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AdvanceSalary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.FloatField()),
                ('reason', models.TextField()),
                ('repayment_months', models.PositiveIntegerField(default=1)),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Head_Approved', 'Head Approved'), ('Approved', 'Approved'), ('Rejected', 'Rejected')], default='Pending', max_length=20)),
                ('head_approved_at', models.DateTimeField(blank=True, null=True)),
                ('hr_approved_at', models.DateTimeField(blank=True, null=True)),
                ('rejection_reason', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='advance_salaries', to='hr.employee')),
                ('head_approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='head_approved_advances', to=settings.AUTH_USER_MODEL)),
                ('hr_approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='hr_approved_advances', to=settings.AUTH_USER_MODEL)),
                ('applied_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='submitted_advances', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
