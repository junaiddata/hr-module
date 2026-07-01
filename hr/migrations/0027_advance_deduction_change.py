from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0026_advance_deduction_tracker'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdvanceDeductionChange',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('old_amount', models.FloatField(blank=True, null=True)),
                ('new_amount', models.FloatField()),
                ('changed_by_role', models.CharField(blank=True, max_length=20)),
                ('note', models.TextField(blank=True)),
                ('changed_at', models.DateTimeField(auto_now_add=True)),
                ('advance', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='deduction_changes',
                    to='hr.advancesalary',
                )),
                ('changed_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='advance_deduction_changes',
                    to='auth.user',
                )),
            ],
            options={
                'ordering': ['changed_at'],
            },
        ),
    ]
