from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("students_management", "0021_room_appointment_room"),
    ]

    operations = [
        migrations.CreateModel(
            name="AppointmentParticipant",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                (
                    "appointment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="participants",
                        to="students_management.appointment",
                    ),
                ),
                (
                    "enrollment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="appointment_participations",
                        to="students_management.enrollment",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="appointmentparticipant",
            constraint=models.UniqueConstraint(
                fields=("appointment", "enrollment"),
                name="unique_appointment_participant",
            ),
        ),
    ]
