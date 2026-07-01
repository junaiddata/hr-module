from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0027_advance_deduction_change'),
    ]

    operations = [
        migrations.CreateModel(
            name='PassportRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.TextField()),
                ('needed_from', models.DateField(blank=True, null=True)),
                ('expected_return', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected'), ('Returned', 'Returned')], default='Pending', max_length=20)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('rejection_reason', models.TextField(blank=True, null=True)),
                ('returned_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='passport_requests', to='hr.employee')),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_passport_requests', to='auth.user')),
                ('returned_marked_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='returned_passport_requests', to='auth.user')),
                ('applied_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='submitted_passport_requests', to='auth.user')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
