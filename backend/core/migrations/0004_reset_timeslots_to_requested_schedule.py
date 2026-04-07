from datetime import time

from django.db import migrations


def reset_timeslots(apps, schema_editor):
    TimeSlot = apps.get_model("core", "TimeSlot")

    TimeSlot.objects.all().delete()

    requested_slots = [
        ("MON", time(hour=9, minute=0), time(hour=17, minute=0)),
        ("TUE", time(hour=9, minute=0), time(hour=17, minute=0)),
        ("WED", time(hour=9, minute=0), time(hour=17, minute=0)),
        ("THU", time(hour=9, minute=0), time(hour=17, minute=0)),
        ("FRI", time(hour=9, minute=0), time(hour=17, minute=0)),
        ("SAT", time(hour=9, minute=0), time(hour=13, minute=0)),
    ]

    for day, start_time, end_time in requested_slots:
        TimeSlot.objects.create(
            day=day,
            start_time=start_time,
            end_time=end_time,
            is_lunch=False,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_batch_subjects"),
    ]

    operations = [
        migrations.RunPython(reset_timeslots, migrations.RunPython.noop),
    ]
