from django.db import migrations


def sync_user_staff_access(apps, schema_editor):
    Staff = apps.get_model('staff_management', 'Staff')

    for staff in Staff.objects.select_related('user').all():
        user = staff.user
        if user is None:
            continue

        user.is_active = staff.is_active and staff.admin_enabled
        user.is_staff = staff.is_active and staff.admin_enabled
        user.is_superuser = (
            staff.is_admin
            and staff.is_active
            and staff.admin_enabled
        )
        user.save(update_fields=['is_active', 'is_staff', 'is_superuser'])


class Migration(migrations.Migration):

    dependencies = [
        ('staff_management', '0005_staff_user'),
    ]

    operations = [
        migrations.RunPython(
            sync_user_staff_access,
            migrations.RunPython.noop,
        ),
    ]