from django.db import migrations, models


DEPT_CHOICES = [
    ('Sales', 'Sales'),
    ('Accounts', 'Accounts'),
    ('Purchase', 'Purchase'),
    ('Office', 'Office'),
    ('Marketing', 'Marketing'),
    ('Shop', 'Shop'),
    ('Foreman', 'Foreman'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0015_multistage_leave_approval'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='department',
            field=models.CharField(
                blank=True,
                choices=DEPT_CHOICES,
                max_length=50,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name='role',
            name='department',
            field=models.CharField(
                blank=True,
                choices=DEPT_CHOICES,
                max_length=50,
                null=True,
            ),
        ),
    ]
