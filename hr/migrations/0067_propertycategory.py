# Generated manually to introduce HR-managed Property Categories (replaces the
# fixed CompanyProperty.category choices with a ForeignKey to a new
# PropertyCategory table).

import django.db.models.deletion
from django.db import migrations, models


LEGACY_CATEGORY_LABELS = {
    'laptop':    'Laptop',
    'desktop':   'Desktop',
    'phone':     'Phone',
    'sim':       'SIM Card',
    'tablet':    'Tablet',
    'furniture': 'Furniture',
    'equipment': 'Equipment',
    'tool':      'Tool',
    'other':     'Other',
}


def seed_categories_and_migrate(apps, schema_editor):
    PropertyCategory = apps.get_model('hr', 'PropertyCategory')
    CompanyProperty = apps.get_model('hr', 'CompanyProperty')

    category_map = {}
    for code, label in LEGACY_CATEGORY_LABELS.items():
        obj, _ = PropertyCategory.objects.get_or_create(name=label)
        category_map[code] = obj

    for prop in CompanyProperty.objects.all():
        prop.category_new = category_map.get(prop.category) if prop.category else None
        prop.save(update_fields=['category_new'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0066_labourcardrenewalprompt'),
    ]

    operations = [
        migrations.CreateModel(
            name='PropertyCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='Category Name')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name_plural': 'Property categories',
            },
        ),
        migrations.AddField(
            model_name='companyproperty',
            name='category_new',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='properties', to='hr.propertycategory'),
        ),
        migrations.RunPython(seed_categories_and_migrate, noop),
        migrations.RemoveField(
            model_name='companyproperty',
            name='category',
        ),
        migrations.RenameField(
            model_name='companyproperty',
            old_name='category_new',
            new_name='category',
        ),
        migrations.AlterField(
            model_name='companyproperty',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='properties', to='hr.propertycategory'),
        ),
    ]
