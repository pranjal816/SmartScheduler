from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_add_default_timeslots"),
    ]

    operations = [
        migrations.AddField(
            model_name="batch",
            name="subjects",
            field=models.ManyToManyField(blank=True, to="core.subject"),
        ),
    ]
