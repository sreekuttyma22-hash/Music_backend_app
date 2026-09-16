from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("staff_management", "0006_sync_user_staff_access"),
        ("students_management", "0023_location_cascade"),
    ]

    operations = [
        migrations.AlterField(
            model_name="staff",
            name="location",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.CASCADE,
                related_name="staff_members",
                to="students_management.location",
            ),
        ),
    ]