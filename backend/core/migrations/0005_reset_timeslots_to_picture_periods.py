from datetime import time

from django.db import migrations


def reset_timeslots_to_picture_periods(apps, schema_editor):
    TimeSlot = apps.get_model("core", "TimeSlot")

    TimeSlot.objects.all().delete()

    periods = [
        (time(hour=9, minute=0), time(hour=9, minute=55)),
        (time(hour=10, minute=0), time(hour=10, minute=55)),
        (time(hour=11, minute=0), time(hour=11, minute=55)),
        (time(hour=12, minute=0), time(hour=12, minute=55)),
        (time(hour=13, minute=0), time(hour=13, minute=55)),
        (time(hour=14, minute=0), time(hour=14, minute=55)),
        (time(hour=15, minute=0), time(hour=15, minute=55)),
        (time(hour=16, minute=0), time(hour=16, minute=55)),
        (time(hour=17, minute=0), time(hour=17, minute=55)),
    ]
    days = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]

    # Create slots period-first so slot ids are interleaved across days.
    # This gives the backtracking engine a more balanced weekly spread.
    for start_time, end_time in periods:
        for day in days:
            TimeSlot.objects.create(
                day=day,
                start_time=start_time,
                end_time=end_time,
                is_lunch=False,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_reset_timeslots_to_requested_schedule"),
    ]

    operations = [
        migrations.RunPython(
            reset_timeslots_to_picture_periods,
            migrations.RunPython.noop,
        ),
    ]
