from django.db import migrations


def rename_dashboard_menu(apps, schema_editor):
    SysMenu = apps.get_model('menu', 'SysMenu')
    SysMenu.objects.filter(
        path='/dashboard',
        perms='system:dashboard:view',
    ).update(name='驾驶舱')


def restore_dashboard_menu_name(apps, schema_editor):
    SysMenu = apps.get_model('menu', 'SysMenu')
    SysMenu.objects.filter(
        path='/dashboard',
        perms='system:dashboard:view',
    ).update(name='首页')


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0008_sysmenu_sibling_unique'),
    ]

    operations = [
        migrations.RunPython(rename_dashboard_menu, restore_dashboard_menu_name),
    ]
