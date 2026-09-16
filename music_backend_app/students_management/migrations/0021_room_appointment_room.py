from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("students_management", "0020_location_remove_course_branch_name_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Room",
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
                ("name", models.CharField(max_length=100)),
                ("capacity", models.PositiveIntegerField(default=1)),
                ("active", models.BooleanField(default=True)),
                (
                    "location",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="rooms",
                        to="students_management.location",
                    ),
                ),
            ],
            options={
                "ordering": ["location", "name"],
            },
        ),
        migrations.AddField(
            model_name="appointment",
            name="room",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="appointments",
                to="students_management.room",
            ),
        ),
        migrations.AddConstraint(
            model_name="room",
            constraint=models.UniqueConstraint(
                fields=("location", "name"),
                name="unique_room_per_location",
            ),
        ),
    ]
