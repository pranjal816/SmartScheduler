from django.db import models
from django.contrib.auth.models import User


class Teacher(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Classroom(models.Model):
    name = models.CharField(max_length=50, unique=True)
    capacity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name} (Cap: {self.capacity})"


class Batch(models.Model):
    name = models.CharField(max_length=50)
    year = models.PositiveIntegerField()
    subjects = models.ManyToManyField("Subject", blank=True)

    class Meta:
        unique_together = ("name", "year")
        ordering = ["year", "name"]

    def __str__(self):
        return f"{self.name} - Year {self.year}"


class Subject(models.Model):
    name = models.CharField(max_length=100)
    lectures_per_week = models.PositiveIntegerField()
    teachers = models.ManyToManyField(Teacher)
    is_lab = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TimeSlot(models.Model):
    DAY_CHOICES = [
        ("MON", "Monday"),
        ("TUE", "Tuesday"),
        ("WED", "Wednesday"),
        ("THU", "Thursday"),
        ("FRI", "Friday"),
        ("SAT", "Saturday"),
    ]

    day = models.CharField(max_length=3, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_lunch = models.BooleanField(default=False)

    class Meta:
        ordering = ["day", "start_time"]

    def __str__(self):
        return f"{self.get_day_display()} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"


class Timetable(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    timeslot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("batch", "timeslot")
        constraints = [
            models.UniqueConstraint(fields=["teacher", "timeslot"], name="unique_teacher_timeslot"),
            models.UniqueConstraint(fields=["classroom", "timeslot"], name="unique_classroom_timeslot"),
        ]

    def __str__(self):
        return f"{self.batch} - {self.subject} @ {self.timeslot}"


class Profile(models.Model):
    ROLE_ADMIN = "admin"
    ROLE_TEACHER = "teacher"
    ROLE_STUDENT = "student"

    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_TEACHER, "Teacher"),
        (ROLE_STUDENT, "Student"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"
