from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Batch, Classroom, Subject, Teacher, Timetable


class Command(BaseCommand):
    help = "Reset the database content to a runnable SmartScheduler demo dataset."

    @transaction.atomic
    def handle(self, *args, **options):
        Timetable.objects.all().delete()
        Batch.objects.all().delete()
        Subject.objects.all().delete()
        Teacher.objects.all().delete()
        Classroom.objects.all().delete()

        teachers = {
            "AKS": Teacher.objects.create(name="AKS"),
            "RKS": Teacher.objects.create(name="RKS"),
            "NVT": Teacher.objects.create(name="NVT"),
            "SMP": Teacher.objects.create(name="SMP"),
            "PDB": Teacher.objects.create(name="PDB"),
            "VKR": Teacher.objects.create(name="VKR"),
            "RJT": Teacher.objects.create(name="RJT"),
            "MAL": Teacher.objects.create(name="MAL"),
        }

        classrooms = [
            Classroom.objects.create(name="CR11", capacity=60),
            Classroom.objects.create(name="LT7", capacity=90),
            Classroom.objects.create(name="LT8", capacity=90),
            Classroom.objects.create(name="LT12", capacity=120),
        ]

        subjects = {}

        def create_subject(name, lectures_per_week, teacher_codes, is_lab=False):
            subject = Subject.objects.create(
                name=name,
                lectures_per_week=lectures_per_week,
                is_lab=is_lab,
            )
            subject.teachers.set([teachers[code] for code in teacher_codes])
            subjects[name] = subject
            return subject

        create_subject("CL111", 3, ["AKS"])
        create_subject("HS171", 3, ["RKS"])
        create_subject("PH111", 4, ["NVT"])
        create_subject("MA111", 3, ["SMP"])
        create_subject("GE171", 3, ["PDB"])
        create_subject("PH171", 2, ["VKR"])
        create_subject("CS101", 4, ["RJT"])
        create_subject("EC105", 3, ["MAL"])

        batch_2a = Batch.objects.create(name="2ndA11", year=2)
        batch_2a.subjects.set(
            [
                subjects["CL111"],
                subjects["HS171"],
                subjects["PH111"],
                subjects["MA111"],
                subjects["GE171"],
                subjects["PH171"],
            ]
        )

        batch_1a = Batch.objects.create(name="1stA07", year=1)
        batch_1a.subjects.set(
            [
                subjects["MA111"],
                subjects["PH111"],
                subjects["CS101"],
                subjects["EC105"],
            ]
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded demo data: {Teacher.objects.count()} teachers, "
                f"{len(classrooms)} classrooms, {Subject.objects.count()} subjects, "
                f"{Batch.objects.count()} batches."
            )
        )
