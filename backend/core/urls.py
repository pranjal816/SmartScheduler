from django.urls import path

from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path("init-db/", views.init_db, name="init_db"),
    path("teacher/add/", views.add_teacher, name="add_teacher"),
    path("classroom/add/", views.add_classroom, name="add_classroom"),
    path("subject/add/", views.add_subject, name="add_subject"),
    path("timeslot/add/", views.add_timeslot, name="add_timeslot"),
    path("batch/add/", views.add_batch, name="add_batch"),
    path("batch/<int:batch_id>/edit/", views.edit_batch, name="edit_batch"),
    path("generate/", views.generate_timetable, name="generate_timetable"),
    path("timetable/", views.timetable_view, name="timetable_view"),
    path("free-classroom/", views.free_classroom_finder, name="free_classroom"),
    path("edit/<int:entry_id>/", views.edit_timetable_entry, name="edit_entry"),
]
