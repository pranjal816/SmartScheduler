# SmartScheduler Project Flow

## 1. Project Purpose

SmartScheduler is a timetable generation system built with Django.

The project allows a user to:

- add teachers
- add classrooms
- add subjects
- assign teachers to subjects
- add batches
- assign subjects to batches
- add time slots
- generate a timetable
- view the timetable in a batchwise grid
- check free classrooms for a selected time slot

The deployed version runs on Vercel and stores data in Neon PostgreSQL.

---

## 2. High-Level Workflow

### Step 1: Master Data Entry

The user first enters the academic data:

- teachers
- classrooms
- subjects
- time slots
- batches

These are created through Django forms and stored in the database.

### Step 2: Batch-Subject Mapping

Each batch is connected to the subjects it studies.

This is important because timetable generation should not assume that every batch studies every subject.

### Step 3: Timetable Generation

When the user clicks **Generate Timetable**:

1. Django loads all batches, their assigned subjects, all classrooms, and all time slots.
2. The Python scheduler creates a conflict-free list of timetable entries.
3. Those entries are saved into the `Timetable` table.
4. The timetable page reads the saved timetable and displays it in a batchwise table.

### Step 4: Timetable Viewing

The user selects a batch from a dropdown.

The app then:

1. loads all timetable entries for that batch
2. arranges them by time row and weekday column
3. renders a timetable similar to the JUIT-style layout

---

## 3. Folder Structure

```text
SmartScheduler/
├── api/
│   ├── index.py
│   └── requirements.txt
├── backend/
│   ├── manage.py
│   ├── core/
│   │   ├── admin.py
│   │   ├── forms.py
│   │   ├── models.py
│   │   ├── scheduler.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── management/
│   │   │   └── commands/
│   │   │       └── seed_demo_data.py
│   │   ├── migrations/
│   │   ├── templates/
│   │   └── static/
│   └── smart_scheduler/
│       ├── settings.py
│       ├── urls.py
│       ├── wsgi.py
│       └── asgi.py
├── cpp_engine/
├── data/
├── docs/
│   ├── PROJECT_FLOW.md
│   └── assets/
│       └── timetable-reference.jpeg
├── public/
├── requirements.txt
├── pyproject.toml
└── vercel.json
```

---

## 4. Core Files and Their Roles

### [backend/core/models.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/models.py)

Defines the database schema:

- `Teacher`
- `Classroom`
- `Subject`
- `Batch`
- `TimeSlot`
- `Timetable`

Important relations:

- a `Subject` has many teachers
- a `Batch` has many subjects
- a `Timetable` row connects one batch, one subject, one teacher, one classroom, and one time slot

### [backend/core/forms.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/forms.py)

Contains Django `ModelForm` classes for:

- teacher entry
- classroom entry
- subject entry
- time slot entry
- batch entry

### [backend/core/views.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/views.py)

Contains the main business logic:

- dashboard view
- data entry views
- timetable generation view
- free classroom finder
- timetable edit view
- protected database initialization route

### [backend/core/scheduler.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/scheduler.py)

Contains the in-process Python timetable generator.

This scheduler:

- loads all tasks for each batch
- tries valid teacher/classroom/timeslot combinations
- avoids teacher conflicts
- avoids classroom conflicts
- avoids batch conflicts
- spreads classes across days and slots in a balanced way

### [backend/core/templates/timetable_view.html](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/templates/timetable_view.html)

Displays the timetable in a batchwise format:

- time ranges on the left
- weekdays across the top
- entries in cells

### [backend/smart_scheduler/settings.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/smart_scheduler/settings.py)

Configures:

- Django settings
- database selection
- static file settings
- Vercel deployment compatibility

### [api/index.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/api/index.py)

This is the Vercel Python entrypoint.

It loads Django’s WSGI application so Vercel can serve the app.

### [vercel.json](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/vercel.json)

Defines routing behavior for Vercel.

All requests are routed to the Django app through `api/index.py`.

---

## 5. Detailed Workflow

## 5.1 Teacher Creation Workflow

1. User opens the **Add Teacher** page.
2. The form submits the teacher name.
3. Django validates the input.
4. If valid, a `Teacher` row is inserted into the database.
5. The page reloads and shows the updated teacher list.

## 5.2 Subject Creation Workflow

1. User opens the **Add Subject** page.
2. User enters:
   - subject name
   - lectures per week
   - assigned teachers
   - whether it is a lab
3. Django saves the `Subject`.
4. Django also creates the many-to-many mapping between subject and selected teachers.

## 5.3 Batch Creation Workflow

1. User opens the **Add Batch** page.
2. User enters:
   - batch name
   - year
   - subjects studied by that batch
3. Django saves the `Batch`.
4. Django stores the many-to-many mapping between batch and subjects.

This mapping is critical for correct timetable generation.

---

## 6. Timetable Generation Code Flow

### Entry Point

The main generation trigger is in:

[backend/core/views.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/views.py)

Inside the `generate_timetable()` view.

### Internal Flow

When `generate_timetable()` runs:

1. It validates that teachers, classrooms, subjects, time slots, and batches exist.
2. It validates that each batch has at least one subject.
3. It loads scheduler input:
   - batches with their subjects and subject teachers
   - classrooms
   - time slots
4. It calls:

```python
generate_timetable_entries(batches, classrooms, timeslots)
```

5. The scheduler returns a list of generated timetable entries.
6. Existing timetable rows are deleted.
7. New timetable rows are inserted into the `Timetable` table.
8. A success message is shown to the user.

### Scheduler Logic

The scheduler creates a list of tasks:

- for each batch
- for each assigned subject
- repeated according to `lectures_per_week`

For each task, it finds the best valid slot by checking:

- batch not already busy in that slot
- teacher not already busy in that slot
- classroom not already busy in that slot

It uses scoring to prefer:

- balanced day distribution
- lower teacher load
- lower room load
- earlier structured slots

---

## 7. Timetable Display Code Flow

### Data Preparation

In `timetable_view()`:

1. all batches are loaded
2. selected batch is read from query string
3. timetable entries for that batch are loaded
4. unique time rows are built
5. a grid is created:
   - row = time range
   - column = weekday

### Rendering

The template:

[backend/core/templates/timetable_view.html](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/templates/timetable_view.html)

renders:

- timetable title
- batch dropdown
- time rows
- weekday headers
- subject/teacher/room content in each cell

The look and feel are styled in:

[backend/core/static/css/custom.css](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/static/css/custom.css)

---

## 8. Database Flow

## 8.1 Main Tables

### `core_teacher`

Stores all teachers.

### `core_classroom`

Stores rooms and capacities.

### `core_subject`

Stores subjects and lecture counts.

### `core_subject_teachers`

Stores many-to-many relation between subjects and teachers.

### `core_batch`

Stores batches.

### `core_batch_subjects`

Stores many-to-many relation between batches and subjects.

### `core_timeslot`

Stores time slot definitions.

### `core_timetable`

Stores generated timetable rows.

Each row in `core_timetable` points to:

- one batch
- one subject
- one teacher
- one classroom
- one time slot

## 8.2 Constraint Flow

The timetable logic respects these constraints:

- one batch cannot have multiple classes in the same slot
- one teacher cannot teach multiple classes in the same slot
- one classroom cannot host multiple classes in the same slot

These are also reinforced at the model/database level for timetable rows.

---

## 9. Deployment Flow

### Local Flow

1. Django runs with `manage.py runserver`
2. SQLite or configured DB is used
3. timetable generation happens inside Django using Python scheduler

### Vercel Flow

1. Vercel receives a request
2. request is routed through [vercel.json](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/vercel.json)
3. `api/index.py` loads Django
4. Django handles the request
5. Neon PostgreSQL stores and serves the data

### Database Initialization Flow

The deployment includes a protected route:

`/init-db/`

This route can:

- run migrations
- optionally seed demo data

It is disabled unless explicitly enabled by environment variable.

---

## 10. Demo Data Flow

The file:

[backend/core/management/commands/seed_demo_data.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/management/commands/seed_demo_data.py)

creates sample:

- teachers
- classrooms
- subjects
- batches
- batch-subject assignments

This is useful for:

- testing locally
- initializing a demo system
- seeing the timetable layout quickly

---

## 11. Reference Screenshot

This is the reference timetable style used while shaping the timetable UI:

![Reference Timetable](./assets/timetable-reference.jpeg)

---

## 12. End-to-End Summary

In simple words, the system works like this:

1. User enters teachers, classrooms, subjects, time slots, and batches.
2. User assigns subjects to batches.
3. User clicks **Generate Timetable**.
4. Django calls the Python scheduler.
5. Scheduler creates conflict-free timetable entries.
6. Entries are saved into the database.
7. User selects a batch and sees the timetable in a visual weekly grid.
8. The same app runs on Vercel using Neon as the production database.

---

## 13. Suggested Future Improvements

- add authentication and admin roles
- support teacher availability preferences
- support lab blocks explicitly
- support different slot durations
- export timetable to PDF
- allow batch/teacher/classroom timetable views
- add drag-and-drop manual timetable adjustment
- add automatic timetable quality scoring
