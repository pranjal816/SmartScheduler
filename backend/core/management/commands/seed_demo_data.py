from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction

from core.scheduler import generate_timetable_entries
from core.models import Batch, Classroom, Profile, Subject, Teacher, Timetable
from core.models import TimeSlot


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

        admin_user, _ = User.objects.get_or_create(username="admin")
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.set_password("admin123")
        admin_user.save()
        admin_user.profile.role = Profile.ROLE_ADMIN
        admin_user.profile.teacher = None
        admin_user.profile.save()

        teacher_user, _ = User.objects.get_or_create(username="aks_teacher")
        teacher_user.set_password("teacher123")
        teacher_user.save()
        teacher_user.profile.role = Profile.ROLE_TEACHER
        teacher_user.profile.teacher = teachers["AKS"]
        teacher_user.profile.save()

        student_user, _ = User.objects.get_or_create(username="student_demo")
        student_user.set_password("student123")
        student_user.save()
        student_user.profile.role = Profile.ROLE_STUDENT
        student_user.profile.teacher = None
        student_user.profile.save()

        generated_entries = generate_timetable_entries(
            list(Batch.objects.prefetch_related("subjects__teachers").order_by("id")),
            list(Classroom.objects.order_by("id")),
            list(TimeSlot.objects.order_by("start_time", "day")),
        )

        for entry in generated_entries:
            Timetable.objects.create(**entry)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded demo data: {Teacher.objects.count()} teachers, "
                f"{len(classrooms)} classrooms, {Subject.objects.count()} subjects, "
                f"{Batch.objects.count()} batches, demo login users, and "
                f"{Timetable.objects.count()} timetable entries."
            )
        )
