from datetime import time

from django.db import migrations, models


def create_default_timeslots(apps, schema_editor):
    TimeSlot = apps.get_model("core", "TimeSlot")

    slot_definitions = [
        ("MON", 9, 17),
        ("TUE", 9, 17),
        ("WED", 9, 17),
        ("THU", 9, 17),
        ("FRI", 9, 17),
        ("SAT", 9, 13),
    ]

    for day, start_hour, end_hour in slot_definitions:
        for hour in range(start_hour, end_hour):
            TimeSlot.objects.get_or_create(
                day=day,
                start_time=time(hour=hour, minute=0),
                end_time=time(hour=hour + 1, minute=0),
                defaults={"is_lunch": False},
            )


def remove_default_timeslots(apps, schema_editor):
    TimeSlot = apps.get_model("core", "TimeSlot")

    slot_definitions = [
        ("MON", 9, 17),
        ("TUE", 9, 17),
        ("WED", 9, 17),
        ("THU", 9, 17),
        ("FRI", 9, 17),
        ("SAT", 9, 13),
    ]

    for day, start_hour, end_hour in slot_definitions:
        for hour in range(start_hour, end_hour):
            TimeSlot.objects.filter(
                day=day,
                start_time=time(hour=hour, minute=0),
                end_time=time(hour=hour + 1, minute=0),
                is_lunch=False,
            ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="timeslot",
            name="day",
            field=models.CharField(
                choices=[
                    ("MON", "Monday"),
                    ("TUE", "Tuesday"),
                    ("WED", "Wednesday"),
                    ("THU", "Thursday"),
                    ("FRI", "Friday"),
                    ("SAT", "Saturday"),
                ],
                max_length=3,
            ),
        ),
        migrations.RunPython(create_default_timeslots, remove_default_timeslots),
    ]
