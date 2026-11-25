from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0072_employeecompanysplit'),
    ]

    operations = [
        migrations.AddField(
            model_name='salarystructure',
            name='car_allowance',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='payrollentry',
            name='car_allowance',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='salaryrevision',
            name='old_car_allowance',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='salaryrevision',
            name='new_car_allowance',
            field=models.FloatField(default=0),
        ),
    ]
