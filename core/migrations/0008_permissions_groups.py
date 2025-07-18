from django.db import migrations


def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    manager, _ = Group.objects.get_or_create(name='Менеджер смен')
    accountant, _ = Group.objects.get_or_create(name='Бухгалтер')
    admin, _ = Group.objects.get_or_create(name='Админ')

    manager_perms = Permission.objects.filter(codename__in=[
        'add_workschedule',
        'change_workschedule',
        'view_workschedule',
        'export_timesheet',
    ])
    accountant_perms = Permission.objects.filter(codename__in=[
        'export_services',
        'export_salary',
    ])
    admin_perms = Permission.objects.filter(content_type__app_label='core')

    manager.permissions.set(manager_perms)
    accountant.permissions.set(accountant_perms)
    admin.permissions.set(admin_perms)


def delete_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=['Менеджер смен', 'Бухгалтер', 'Админ']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_scheduletemplate'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='employee',
            options={'permissions': [('import_employees', 'Can import employees from Excel')]},
        ),
        migrations.AlterModelOptions(
            name='workschedule',
            options={
                'unique_together': {('employee', 'date')},
                'permissions': [
                    ('export_timesheet', 'Can export timesheet'),
                    ('export_salary', 'Can export salary reports'),
                ],
            },
        ),
        migrations.AlterModelOptions(
            name='employeeservicerecord',
            options={
                'unique_together': {('employee', 'service', 'month')},
                'permissions': [('export_services', 'Can export services')],
            },
        ),
        migrations.RunPython(create_groups, delete_groups),
    ]
