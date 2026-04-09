from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Batch, Classroom, Profile, Subject, Teacher, TimeSlot, Timetable


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "capacity")
    search_fields = ("name",)


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "year")
    list_filter = ("year",)
    search_fields = ("name",)
    filter_horizontal = ("subjects",)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "lectures_per_week", "is_lab")
    list_filter = ("is_lab",)
    search_fields = ("name",)
    filter_horizontal = ("teachers",)


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ("id", "day", "start_time", "end_time", "is_lunch")
    list_filter = ("day", "is_lunch")


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ("id", "batch", "subject", "teacher", "classroom", "timeslot")
    list_filter = ("batch", "timeslot__day")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "teacher")
    list_filter = ("role",)
    search_fields = ("user__username", "teacher__name")


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
