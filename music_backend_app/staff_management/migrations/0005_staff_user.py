from django.conf import settings
from django.db import migrations, models


def create_users_for_existing_staff(apps, schema_editor):
    Staff = apps.get_model('staff_management', 'Staff')
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))

    for staff in Staff.objects.all():
        user = User.objects.create(
            username=staff.email[:150],
            first_name=staff.first_name,
            last_name=staff.last_name,
            email=staff.email,
            is_active=staff.is_active and staff.admin_enabled,
            is_staff=staff.admin_enabled and staff.is_active,
            is_superuser=staff.is_admin and staff.admin_enabled and staff.is_active,
        )
        user.password = staff.password or '!'
        user.save(update_fields=['password'])
        staff.user_id = user.pk
        staff.save(update_fields=['user'])


class Migration(migrations.Migration):

    dependencies = [
        ('staff_management', '0004_staff_address_staff_date_of_birth_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='staff',
            name='user',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=models.CASCADE,
                related_name='staff_profile',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(
            create_users_for_existing_staff,
            migrations.RunPython.noop,
        ),
    ]