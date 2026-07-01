from django.db import migrations


def convert_old_roles(apps, schema_editor):
    Role = apps.get_model('hr', 'Role')
    # Admin becomes HR (final approver — equivalent responsibility)
    Role.objects.filter(role='Admin').update(role='HR')
    # Employee role records are no longer valid — remove them
    Role.objects.filter(role='Employee').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0017_four_stage_approval'),
    ]

    operations = [
        migrations.RunPython(convert_old_roles, migrations.RunPython.noop),
    ]
