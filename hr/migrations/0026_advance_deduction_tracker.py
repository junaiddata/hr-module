from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0025_advance_salary'),
    ]

    operations = [
        # AdvanceSalary: swap repayment_months for two new deduction fields
        migrations.RemoveField(
            model_name='advancesalary',
            name='repayment_months',
        ),
        migrations.AddField(
            model_name='advancesalary',
            name='requested_monthly_deduction',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='advancesalary',
            name='approved_monthly_deduction',
            field=models.FloatField(null=True, blank=True),
        ),
        # PayrollEntry: advance deduction tracking
        migrations.AddField(
            model_name='payrollentry',
            name='advance_deduction',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='payrollentry',
            name='advance_salary',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='payroll_deductions',
                to='hr.advancesalary',
            ),
        ),
    ]
