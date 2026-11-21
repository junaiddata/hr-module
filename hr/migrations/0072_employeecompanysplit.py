import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0071_notificationcomment'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmployeeCompanySplit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('percentage', models.DecimalField(decimal_places=2, max_digits=5)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='company_splits', to='hr.employee')),
                ('mol', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employee_splits', to='hr.mol')),
            ],
            options={
                'ordering': ['-percentage', 'mol__mol'],
                'unique_together': {('employee', 'mol')},
            },
        ),
    ]
