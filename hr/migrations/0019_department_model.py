from django.db import migrations, models
import django.db.models.deletion


DEFAULT_DEPARTMENTS = ['Sales', 'Accounts', 'Purchase', 'Office', 'Marketing', 'Shop', 'Foreman']


def migrate_departments(apps, schema_editor):
    Employee = apps.get_model('hr', 'Employee')
    Role = apps.get_model('hr', 'Role')
    Department = apps.get_model('hr', 'Department')

    # Seed the default departments
    dept_map = {}
    for name in DEFAULT_DEPARTMENTS:
        dept, _ = Department.objects.get_or_create(name=name)
        dept_map[name] = dept

    # Pick up any extra values already in the DB
    for emp in Employee.objects.exclude(department_old='').exclude(department_old__isnull=True):
        name = emp.department_old.strip()
        if name and name not in dept_map:
            dept, _ = Department.objects.get_or_create(name=name)
            dept_map[name] = dept

    for role in Role.objects.exclude(department_old='').exclude(department_old__isnull=True):
        name = role.department_old.strip()
        if name and name not in dept_map:
            dept, _ = Department.objects.get_or_create(name=name)
            dept_map[name] = dept

    # Link employees
    for emp in Employee.objects.all():
        old = (emp.department_old or '').strip()
        if old in dept_map:
            emp.department = dept_map[old]
            emp.save()

    # Link roles
    for role in Role.objects.all():
        old = (role.department_old or '').strip()
        if old in dept_map:
            role.department = dept_map[old]
            role.save()


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0018_fix_existing_roles'),
    ]

    operations = [
        # 1. Create Department model
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),

        # 2. Rename existing CharField to _old so we can add FK named department
        migrations.RenameField(model_name='employee', old_name='department', new_name='department_old'),
        migrations.RenameField(model_name='role',     old_name='department', new_name='department_old'),

        # 3. Add new FK fields
        migrations.AddField(
            model_name='employee',
            name='department',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='hr.Department',
            ),
        ),
        migrations.AddField(
            model_name='role',
            name='department',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='hr.Department',
            ),
        ),

        # 4. Data migration: create Department records and link rows
        migrations.RunPython(migrate_departments, migrations.RunPython.noop),

        # 5. Drop the old CharField columns
        migrations.RemoveField(model_name='employee', name='department_old'),
        migrations.RemoveField(model_name='role',     name='department_old'),
    ]
