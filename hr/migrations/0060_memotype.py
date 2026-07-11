# Generated manually to introduce HR-managed Memo Types (replaces the fixed
# memo_type choices with a ForeignKey to a new MemoType table).

import django.db.models.deletion
from django.db import migrations, models


LEGACY_TYPE_LABELS = {
    'holiday':            'National Holiday Declaration',
    'warning_employee':   'Warning to Employee',
    'warning_department': 'Warning to Department',
    'general':            'General Memo to All Staff',
}


def seed_memo_types_and_migrate(apps, schema_editor):
    MemoType = apps.get_model('hr', 'MemoType')
    Memo = apps.get_model('hr', 'Memo')

    type_map = {}
    for code, label in LEGACY_TYPE_LABELS.items():
        obj, _ = MemoType.objects.get_or_create(memo_type=label)
        type_map[code] = obj
    default_type = type_map['general']

    for memo in Memo.objects.all():
        memo.memo_type_new = type_map.get(memo.memo_type, default_type)
        memo.save(update_fields=['memo_type_new'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0059_memo'),
    ]

    operations = [
        migrations.CreateModel(
            name='MemoType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('memo_type', models.CharField(max_length=60, unique=True, verbose_name='Memo Type')),
            ],
            options={
                'ordering': ['memo_type'],
            },
        ),
        migrations.AddField(
            model_name='memo',
            name='memo_type_new',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='memos', to='hr.memotype'),
        ),
        migrations.RunPython(seed_memo_types_and_migrate, noop),
        migrations.RemoveField(
            model_name='memo',
            name='memo_type',
        ),
        migrations.RenameField(
            model_name='memo',
            old_name='memo_type_new',
            new_name='memo_type',
        ),
        migrations.AlterField(
            model_name='memo',
            name='memo_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='memos', to='hr.memotype'),
        ),
    ]
