import json
import os
import subprocess
from functools import wraps
from json import JSONDecodeError

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.management import call_command
from django.db import models, transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .scheduler import generate_timetable_entries
from .forms import BatchForm, ClassroomForm, LoginForm, SubjectForm, TeacherForm, TimeSlotForm
from .models import Batch, Classroom, Profile, Subject, Teacher, TimeSlot, Timetable


def _user_role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser or user.is_staff:
        return Profile.ROLE_ADMIN
    profile = getattr(user, "profile", None)
    return profile.role if profile else Profile.ROLE_STUDENT


def _is_admin(user):
    return _user_role(user) == Profile.ROLE_ADMIN


def _is_teacher(user):
    return _user_role(user) == Profile.ROLE_TEACHER


def _is_student(user):
    return _user_role(user) == Profile.ROLE_STUDENT


def _teacher_for_user(user):
    return getattr(getattr(user, "profile", None), "teacher", None)


def role_required(*allowed_roles):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            role = _user_role(request.user)
            if role not in allowed_roles:
                messages.error(request, "You do not have permission to access that page.")
                return redirect("index")
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


class UserLoginView(LoginView):
    template_name = "login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        role = _user_role(self.request.user)
        if role in {Profile.ROLE_TEACHER, Profile.ROLE_STUDENT}:
            return "/timetable/"
        return "/"


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")


@login_required
def index(request):
    role = _user_role(request.user)
    if role in {Profile.ROLE_TEACHER, Profile.ROLE_STUDENT}:
        return redirect("timetable_view")

    context = {
        "teacher_count": Teacher.objects.count(),
        "classroom_count": Classroom.objects.count(),
        "subject_count": Subject.objects.count(),
        "timeslot_count": TimeSlot.objects.count(),
        "batch_count": Batch.objects.count(),
        "user_role": role,
    }
    return render(request, "index.html", context)


def init_db(request):
    if os.environ.get("ENABLE_DB_INIT_ROUTE", "False").lower() != "true":
        return JsonResponse({"error": "Not found."}, status=404)

    expected_token = os.environ.get("INIT_DB_TOKEN")
    supplied_token = request.GET.get("token")

    if not expected_token:
        return JsonResponse({"error": "INIT_DB_TOKEN is not configured."}, status=500)

    if supplied_token != expected_token:
        return JsonResponse({"error": "Unauthorized."}, status=401)

    try:
        call_command("migrate", interactive=False, verbosity=1)
        if request.GET.get("seed") == "1":
            call_command("seed_demo_data", verbosity=1)
        return HttpResponse("Database initialization completed successfully.")
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)


@role_required(Profile.ROLE_ADMIN)
def add_teacher(request):
    if request.method == "POST":
        form = TeacherForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Teacher added successfully!")
            return redirect("add_teacher")
    else:
        form = TeacherForm()
    teachers = Teacher.objects.order_by("name")
    return render(request, "teacher_form.html", {"form": form, "teachers": teachers})


@role_required(Profile.ROLE_ADMIN)
def add_classroom(request):
    if request.method == "POST":
        form = ClassroomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Classroom added successfully!")
            return redirect("add_classroom")
    else:
        form = ClassroomForm()
    classrooms = Classroom.objects.order_by("name")
    return render(request, "classroom_form.html", {"form": form, "classrooms": classrooms})


@role_required(Profile.ROLE_ADMIN)
def add_subject(request):
    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f"Subject {subject.name} added successfully!")
            return redirect("add_subject")
    else:
        form = SubjectForm()
    subjects = Subject.objects.prefetch_related("teachers").order_by("name")
    return render(request, "subject_form.html", {"form": form, "subjects": subjects})


@role_required(Profile.ROLE_ADMIN)
def add_timeslot(request):
    if request.method == "POST":
        form = TimeSlotForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Time slot added successfully!")
            return redirect("add_timeslot")
    else:
        form = TimeSlotForm()
    timeslots = TimeSlot.objects.all()
    return render(request, "timeslot_form.html", {"form": form, "timeslots": timeslots})


@role_required(Profile.ROLE_ADMIN)
def add_batch(request):
    if request.method == "POST":
        form = BatchForm(request.POST)
        if form.is_valid():
            batch = form.save()
            messages.success(request, "Batch added successfully!")
            return redirect("add_batch")
    else:
        form = BatchForm()
    batches = Batch.objects.prefetch_related("subjects").all()
    return render(request, "batch_form.html", {"form": form, "batches": batches})


@role_required(Profile.ROLE_ADMIN)
def edit_batch(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)

    if request.method == "POST":
        form = BatchForm(request.POST, instance=batch)
        if form.is_valid():
            form.save()
            messages.success(request, "Batch updated successfully!")
            return redirect("add_batch")
    else:
        form = BatchForm(instance=batch)

    batches = Batch.objects.prefetch_related("subjects").all()
    return render(
        request,
        "batch_form.html",
        {"form": form, "batches": batches, "editing_batch": batch},
    )


def _ordered_subjects():
    return Subject.objects.prefetch_related("teachers").order_by("id")


def _ordered_batches():
    return Batch.objects.order_by("id")


def _ordered_teachers():
    return Teacher.objects.order_by("id")


def _ordered_classrooms():
    return Classroom.objects.order_by("id")


def _ordered_timeslots():
    return TimeSlot.objects.order_by("id")


def _scheduler_input():
    return {
        "batches": list(Batch.objects.prefetch_related("subjects__teachers").order_by("id")),
        "classrooms": list(Classroom.objects.order_by("id")),
        "timeslots": list(TimeSlot.objects.order_by("start_time", "day")),
    }


def generate_input_json():
    subjects = []
    subject_index_map = {}
    teacher_index_map = {
        teacher.id: index for index, teacher in enumerate(_ordered_teachers())
    }
    for subject in _ordered_subjects():
        subject_index_map[subject.id] = len(subjects)
        subjects.append(
            {
                "teachers": [
                    teacher_index_map[teacher.id]
                    for teacher in subject.teachers.order_by("id")
                    if teacher.id in teacher_index_map
                ],
                "lectures": subject.lectures_per_week,
                "is_lab": subject.is_lab,
            }
        )

    batch_subjects = []
    for batch in Batch.objects.prefetch_related("subjects").order_by("id"):
        batch_subjects.append(
            [subject_index_map[subject.id] for subject in batch.subjects.order_by("id") if subject.id in subject_index_map]
        )

    timeslots = list(_ordered_timeslots())
    lunch_slots = [index for index, slot in enumerate(timeslots) if slot.is_lunch]

    data = {
        "subjects": subjects,
        "rooms": Classroom.objects.count(),
        "slots": len(timeslots),
        "batches": Batch.objects.count(),
        "batch_subjects": batch_subjects,
        "teachers": Teacher.objects.count(),
        "lunch_slots": lunch_slots,
    }

    os.makedirs(settings.DATA_DIR, exist_ok=True)
    input_path = os.path.join(settings.DATA_DIR, "input.json")
    with open(input_path, "w", encoding="utf-8") as file_handle:
        json.dump(data, file_handle, indent=2)

    return input_path


def run_cpp_engine():
    try:
        result = subprocess.run(
            [settings.CPP_ENGINE_PATH],
            cwd=os.path.dirname(settings.CPP_ENGINE_PATH),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        return result.returncode == 0, result.stderr.strip() or result.stdout.strip()
    except Exception as exc:
        return False, str(exc)


def load_output_json():
    output_path = os.path.join(settings.DATA_DIR, "output.json")
    if not os.path.exists(output_path):
        return None
    try:
        with open(output_path, "r", encoding="utf-8") as file_handle:
            return json.load(file_handle)
    except JSONDecodeError:
        return None


@transaction.atomic
def save_timetable_from_output(output_data):
    Timetable.objects.all().delete()

    batches = list(_ordered_batches())
    subjects = list(_ordered_subjects())
    teachers = list(_ordered_teachers())
    classrooms = list(_ordered_classrooms())
    timeslots = list(_ordered_timeslots())

    for entry in output_data.get("timetable", []):
        Timetable.objects.create(
            batch=batches[entry["batch"]],
            subject=subjects[entry["subject"]],
            teacher=teachers[entry["teacher"]],
            classroom=classrooms[entry["room"]],
            timeslot=timeslots[entry["slot"]],
        )


@transaction.atomic
def save_timetable_entries(entries):
    Timetable.objects.all().delete()
    for entry in entries:
        Timetable.objects.create(**entry)


@role_required(Profile.ROLE_ADMIN)
def generate_timetable(request):
    if request.method != "POST":
        return redirect("index")

    if Teacher.objects.count() == 0:
        messages.error(request, "Add at least one teacher first.")
    elif Classroom.objects.count() == 0:
        messages.error(request, "Add at least one classroom first.")
    elif Subject.objects.count() == 0:
        messages.error(request, "Add at least one subject first.")
    elif TimeSlot.objects.count() == 0:
        messages.error(request, "Add at least one time slot first.")
    elif Batch.objects.count() == 0:
        messages.error(request, "Add at least one batch first.")
    elif Batch.objects.filter(subjects__isnull=True).exists():
        messages.error(request, "Assign at least one subject to every batch before generating the timetable.")
    else:
        scheduler_input = _scheduler_input()
        generated_entries = generate_timetable_entries(
            scheduler_input["batches"],
            scheduler_input["classrooms"],
            scheduler_input["timeslots"],
        )
        if generated_entries:
            save_timetable_entries(generated_entries)
            messages.success(request, "Timetable generated successfully!")
        else:
            messages.error(
                request,
                "Unable to generate a timetable with the current teachers, subjects, classrooms, and time slots.",
            )

    return redirect("timetable_view")


@role_required(Profile.ROLE_ADMIN, Profile.ROLE_TEACHER, Profile.ROLE_STUDENT)
def timetable_view(request):
    batches = Batch.objects.all()
    selected_batch_id = request.GET.get("batch")
    timetable_entries = Timetable.objects.none()
    timeslots = TimeSlot.objects.all()

    if not selected_batch_id and (_is_teacher(request.user) or _is_student(request.user)):
        first_batch = None
        if _is_teacher(request.user):
            teacher = _teacher_for_user(request.user)
            if teacher is not None:
                first_batch = (
                    Batch.objects.filter(timetable__teacher=teacher)
                    .distinct()
                    .order_by("year", "name")
                    .first()
                )
        if first_batch is None:
            first_batch = batches.first()
        if first_batch:
            return redirect(f"/timetable/?batch={first_batch.id}")

    if selected_batch_id:
        batch = get_object_or_404(Batch, id=selected_batch_id)
        timetable_entries = Timetable.objects.filter(batch=batch).select_related(
            "subject", "teacher", "classroom", "timeslot"
        )

    days = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
    day_labels = {
        "MON": "Monday",
        "TUE": "Tuesday",
        "WED": "Wednesday",
        "THU": "Thursday",
        "FRI": "Friday",
        "SAT": "Saturday",
    }
    time_rows = []
    seen_time_keys = set()
    for timeslot in timeslots:
        time_key = (
            timeslot.start_time.strftime("%H:%M"),
            timeslot.end_time.strftime("%H:%M"),
        )
        if time_key not in seen_time_keys:
            seen_time_keys.add(time_key)
            time_rows.append(
                {
                    "key": f"{time_key[0]}-{time_key[1]}",
                    "start": time_key[0],
                    "end": time_key[1],
                }
            )

    grid = {row["key"]: {day: None for day in days} for row in time_rows}

    for entry in timetable_entries:
        row_key = (
            f"{entry.timeslot.start_time.strftime('%H:%M')}-"
            f"{entry.timeslot.end_time.strftime('%H:%M')}"
        )
        if row_key in grid and entry.timeslot.day in grid[row_key]:
            grid[row_key][entry.timeslot.day] = entry

    context = {
        "batches": batches,
        "selected_batch_id": int(selected_batch_id) if selected_batch_id else None,
        "time_rows": time_rows,
        "days": days,
        "day_labels": day_labels,
        "grid": grid,
        "can_edit_entries": _is_admin(request.user) or _is_teacher(request.user),
        "is_admin_user": _is_admin(request.user),
        "teacher_id": _teacher_for_user(request.user).id if _teacher_for_user(request.user) else None,
    }
    return render(request, "timetable_view.html", context)


@role_required(Profile.ROLE_ADMIN, Profile.ROLE_TEACHER)
def free_classroom_finder(request):
    timeslots = TimeSlot.objects.all()
    available_classrooms = []
    selected_timeslot = None

    if request.method == "POST":
        timeslot_id = request.POST.get("timeslot")
        if timeslot_id:
            selected_timeslot = get_object_or_404(TimeSlot, id=timeslot_id)
            busy_classrooms = Timetable.objects.filter(timeslot=selected_timeslot).values_list(
                "classroom", flat=True
            )
            available_classrooms = Classroom.objects.exclude(id__in=busy_classrooms)

    return render(
        request,
        "free_classroom.html",
        {
            "timeslots": timeslots,
            "available_classrooms": available_classrooms,
            "selected_timeslot": selected_timeslot,
        },
    )


@role_required(Profile.ROLE_ADMIN, Profile.ROLE_TEACHER)
def edit_timetable_entry(request, entry_id):
    entry = get_object_or_404(Timetable, id=entry_id)

    if _is_teacher(request.user):
        teacher = _teacher_for_user(request.user)
        if teacher is None or entry.teacher_id != teacher.id:
            messages.error(request, "You can only reschedule your own classes.")
            return redirect(f"/timetable/?batch={entry.batch.id}")

    if request.method == "POST":
        new_timeslot_id = request.POST.get("timeslot")
        new_classroom_id = request.POST.get("classroom")

        if new_timeslot_id and new_classroom_id:
            new_timeslot = get_object_or_404(TimeSlot, id=new_timeslot_id)
            new_classroom = get_object_or_404(Classroom, id=new_classroom_id)

            conflict = (
                Timetable.objects.filter(timeslot=new_timeslot)
                .filter(
                    models.Q(batch=entry.batch)
                    | models.Q(teacher=entry.teacher)
                    | models.Q(classroom=new_classroom)
                )
                .exclude(id=entry.id)
                .exists()
            )

            if not conflict:
                entry.timeslot = new_timeslot
                entry.classroom = new_classroom
                entry.save()
                messages.success(request, "Entry updated successfully.")
            else:
                messages.error(
                    request,
                    "Conflict detected: batch, teacher, or classroom is already occupied at that time.",
                )

        batch_id = request.GET.get("batch", entry.batch.id)
        return redirect(f"/timetable/?batch={batch_id}")

    timeslots = TimeSlot.objects.all()
    classrooms = Classroom.objects.all()
    return render(
        request,
        "edit_timetable.html",
        {"entry": entry, "timeslots": timeslots, "classrooms": classrooms},
    )
