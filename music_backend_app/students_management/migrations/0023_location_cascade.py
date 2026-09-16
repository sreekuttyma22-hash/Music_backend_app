from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("students_management", "0022_appointmentparticipant"),
        ("staff_management", "0006_sync_user_staff_access"),
    ]

    operations = [
        migrations.AlterField(
            model_name="room",
            name="location",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name="rooms",
                to="students_management.location",
            ),
        ),
        migrations.AlterField(
            model_name="student",
            name="location",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.CASCADE,
                related_name="students",
                to="students_management.location",
            ),
        ),
        migrations.AlterField(
            model_name="instructor",
            name="location",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.CASCADE,
                related_name="instructors",
                to="students_management.location",
            ),
        ),
        migrations.AlterField(
            model_name="enrollment",
            name="location",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.CASCADE,
                related_name="enrollments",
                to="students_management.location",
            ),
        ),
        migrations.AlterField(
            model_name="appointment",
            name="location",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.CASCADE,
                related_name="appointments",
                to="students_management.location",
            ),
        ),
        migrations.AlterField(
            model_name="appointment",
            name="room",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.CASCADE,
                related_name="appointments",
                to="students_management.room",
            ),
        ),
    ]