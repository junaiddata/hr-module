from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0028_passport_request'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='passport_status',
            field=models.CharField(
                choices=[('With company', 'With Company'), ('With employee', 'With Employee')],
                default='With company',
                max_length=20,
            ),
        ),
    ]
