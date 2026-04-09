# SmartScheduler System Diagrams Explained In Words

This document explains the system design of SmartScheduler in plain language.

It is based on the actual project files currently present in the repository, especially:

- [backend/core/models.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/models.py)
- [backend/core/views.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/views.py)
- [backend/core/scheduler.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/scheduler.py)
- [backend/core/forms.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/forms.py)
- [backend/core/urls.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/urls.py)
- [backend/smart_scheduler/settings.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/smart_scheduler/settings.py)
- [api/index.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/api/index.py)
- [vercel.json](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/vercel.json)
- [backend/core/management/commands/seed_demo_data.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/management/commands/seed_demo_data.py)

Important note:

The repository still contains the older C++ engine files in [cpp_engine/scheduler.cpp](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/cpp_engine/scheduler.cpp) and JSON handoff helpers in [backend/core/views.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/views.py), but the active timetable generation flow in the web app now uses the Python scheduler from [backend/core/scheduler.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/scheduler.py). This document describes the current active system first, and then notes the inactive legacy path where relevant.

---

## 1. System Overview

SmartScheduler is a Django application for creating and viewing academic timetables.

At a high level:

1. The user enters master data such as teachers, classrooms, subjects, time slots, and batches.
2. The user links subjects to batches.
3. The user clicks the timetable generation action.
4. Django loads batches, subjects, teachers, classrooms, and time slots from the database.
5. The Python scheduler creates valid timetable entries while avoiding conflicts.
6. Django stores the result in the `Timetable` table.
7. The user opens the timetable page and sees a batchwise schedule laid out as time rows and weekday columns.

The deployed version runs on Vercel and uses Neon PostgreSQL.

---

## 2. Activity Diagram Explained In Words

An activity diagram describes what activities happen in the system and in what order.

### Main User Activity Flow

The main activity flow of SmartScheduler is:

1. Start the application.
2. Open the dashboard.
3. Enter academic resources.
4. Enter teaching structure.
5. Generate timetable.
6. View or edit timetable.
7. Check free classrooms if needed.

### Detailed Activity Flow

#### Activity Group 1: Data Setup

The system begins with setup activities:

- add teacher
- add classroom
- add subject
- add time slot
- add batch
- assign subjects to the batch

These activities are independent data-entry tasks, but together they create the input required for timetable generation.

#### Activity Group 2: Validation Before Generation

When the user clicks the generate action in [backend/core/views.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/views.py), the system performs a sequence of checks:

- are there any teachers?
- are there any classrooms?
- are there any subjects?
- are there any time slots?
- are there any batches?
- does every batch have at least one assigned subject?

If any of these checks fail, the activity flow stops and a message is shown to the user.

#### Activity Group 3: Timetable Generation

If validation succeeds:

1. Django collects scheduler input.
2. The scheduler builds a task list.
3. Each task represents one lecture instance for a batch-subject combination.
4. The scheduler searches for a valid teacher, classroom, and time slot.
5. If a valid assignment is found, it is added to the result.
6. If no valid assignment is found for a task, generation fails and an error is shown.
7. If all tasks are assigned successfully, the old timetable is deleted and the new timetable is saved.

#### Activity Group 4: Timetable Consumption

After generation:

- the user may open the timetable page
- the user may choose a batch from a dropdown
- the system displays only that batch’s timetable
- the user may edit an entry or check free classrooms

### Decision Points In The Activity Flow

The major decision points are:

- valid form or invalid form
- missing required master data or complete master data
- generation success or generation failure
- conflict found while editing or no conflict found while editing

So in words, the activity diagram is a structured flow from setup, to validation, to generation, to viewing/editing.

---

## 3. Class Diagram Explained In Words

A class diagram shows the main entities in the system, their attributes, and how they are related.

The real class structure is defined in [backend/core/models.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/models.py).

### Teacher

Represents a teacher.

Main attribute:

- `name`

Meaning:

- a teacher is a resource that can teach one or more subjects

### Classroom

Represents a physical classroom.

Main attributes:

- `name`
- `capacity`

Meaning:

- a classroom is a resource where a lecture can happen

### Subject

Represents an academic subject.

Main attributes:

- `name`
- `lectures_per_week`
- `is_lab`

Relationships:

- many-to-many with `Teacher`

Meaning:

- a subject needs one or more teachers
- a subject contributes repeated lecture tasks during timetable generation

### Batch

Represents a student group such as a section or year-group.

Main attributes:

- `name`
- `year`

Relationships:

- many-to-many with `Subject`

Meaning:

- each batch studies a specific set of subjects
- this mapping is essential for correct timetable generation

### TimeSlot

Represents one schedulable period.

Main attributes:

- `day`
- `start_time`
- `end_time`
- `is_lunch`

Meaning:

- time slots are the positions available in the weekly schedule

### Timetable

Represents one final scheduled class entry.

Relationships:

- foreign key to `Batch`
- foreign key to `Subject`
- foreign key to `Teacher`
- foreign key to `Classroom`
- foreign key to `TimeSlot`

Meaning:

- one `Timetable` row is one concrete scheduled class

### Key Relationships Between Classes

In plain language, the class relationships are:

- one subject can have many teachers
- one teacher can teach many subjects
- one batch can study many subjects
- one subject can belong to many batches
- one timetable entry belongs to exactly one batch, one subject, one teacher, one classroom, and one time slot

### Constraint Meaning In The Class Model

The class model also enforces rules:

- one batch cannot have two timetable entries in the same time slot
- one teacher cannot have two timetable entries in the same time slot
- one classroom cannot have two timetable entries in the same time slot

This means the class diagram is not just structural. It also encodes scheduling constraints.

---

## 4. Sequence Diagram Explained In Words

A sequence diagram explains the order in which objects interact during a specific scenario.

The most important sequence in this system is timetable generation.

### Sequence: Generate Timetable

Actor:

- User

Participants:

- Browser
- Django view (`generate_timetable`)
- Scheduler (`generate_timetable_entries`)
- Database

### Sequence Steps

1. The user clicks the generate button from the dashboard or a page that posts to the timetable generation route.
2. The browser sends a POST request to Django.
3. Django enters `generate_timetable()` in [backend/core/views.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/views.py).
4. The view queries the database to count teachers, classrooms, subjects, time slots, and batches.
5. The view checks whether any batch has no assigned subjects.
6. If validation fails, the view sets an error message and redirects the user.
7. If validation succeeds, the view loads:
   - batches with subjects and teachers
   - classrooms
   - time slots
8. The view calls the scheduler function in [backend/core/scheduler.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/scheduler.py).
9. The scheduler creates a task list.
10. The scheduler iterates through the tasks and tries valid assignments.
11. The scheduler returns either:
    - a list of timetable entries, or
    - an empty result indicating failure
12. If entries are returned, Django deletes previous timetable rows.
13. Django inserts new timetable rows into the database.
14. Django sets a success message.
15. Django redirects to the timetable view.
16. The browser requests the timetable page.
17. Django renders the saved timetable entries in a grid.

### Sequence: View Timetable

1. User selects a batch.
2. Browser sends a GET request with `batch=<id>`.
3. Django loads the selected batch timetable entries.
4. Django builds a grid grouped by time rows and weekdays.
5. Django renders the timetable template.

### Sequence: Edit Timetable Entry

1. User opens edit page for one timetable entry.
2. Django loads that timetable row.
3. User selects new classroom and time slot.
4. Browser sends POST request.
5. Django checks conflict rules:
   - same batch at same time?
   - same teacher at same time?
   - same classroom at same time?
6. If no conflict exists, Django saves the update.
7. Otherwise, Django shows an error message.

So the sequence diagram for this project is mainly request-driven: browser request, view execution, scheduler/database interaction, response rendering.

---

## 5. Collaboration Diagram Explained In Words

A collaboration diagram explains which objects work together and what each one contributes.

In SmartScheduler, the main collaborators are:

- Django views
- Django models
- Django forms
- scheduler module
- templates
- database
- Vercel runtime

### Collaboration Around Data Entry

When a user submits a form:

- the form class validates user input
- the view controls the request/response logic
- the model represents the stored data
- the database stores the row
- the template renders the page and form errors or success messages

So during data entry, forms, views, models, and templates collaborate closely.

### Collaboration Around Timetable Generation

During generation:

- the view orchestrates the whole process
- the model layer supplies the entities
- the scheduler applies the allocation logic
- the database stores the final entries
- the message framework communicates success/failure back to the user

The scheduler itself does not talk to the browser directly.
It collaborates with the view by receiving model objects and returning plain assignment data.

### Collaboration Around Deployment

In deployed mode:

- Vercel receives the HTTP request
- `api/index.py` loads the Django WSGI app
- Django resolves the URL and calls the correct view
- the view collaborates with the database and templates
- Neon stores persistent production data

### Collaboration Around Demo Initialization

When the protected DB initialization route is enabled:

- a request reaches the Django route
- the view checks token and environment state
- Django management commands run migrations and optional demo seeding
- the database schema and demo rows are created

So the collaboration diagram in this project is very centered around the Django view layer coordinating all other parts.

---

## 6. State Diagram Explained In Words

A state diagram explains how something changes state over time.

The most meaningful object to describe with states here is the timetable itself.

### Timetable States

#### State 1: Not Initialized

No timetable rows exist in the database.

This can happen when:

- the project is fresh
- the database was just created
- timetable generation has never been run

#### State 2: Ready For Generation

The required master data exists:

- teachers
- classrooms
- subjects
- time slots
- batches
- batch-subject mapping

The timetable is now eligible to be generated.

#### State 3: Generation In Progress

The user has triggered timetable generation.

At this state:

- validation is running
- scheduler input is being prepared
- the scheduler is assigning entries

#### State 4: Generation Failed

The scheduler could not produce valid entries.

Reasons can include:

- missing data
- empty batch-subject mappings
- impossible resource constraints

The system returns to a state where the user must fix data and try again.

#### State 5: Generated

A valid timetable exists in the `Timetable` table.

At this point:

- the timetable can be viewed
- entries can be edited
- free classroom checks can use the saved timetable

#### State 6: Edited

After manual entry editing:

- the timetable still exists
- one or more rows have changed

The timetable remains in a valid active state as long as conflicts are prevented.

### Batch State Perspective

A `Batch` also has meaningful states:

- created but no subjects assigned
- ready for scheduling after subject assignment
- scheduled after timetable generation

### Deployment State Perspective

The deployed app also moves through states:

- deployed but DB not initialized
- DB initialized
- app ready for normal use

So the state diagram in words is mostly about the lifecycle of data completeness and timetable availability.

---

## 7. Component Diagram Explained In Words

A component diagram explains the major software parts and how they connect.

### Component 1: Browser / User Interface

The browser is the user-facing component.

It interacts with:

- forms
- timetable page
- classroom finder page
- batch edit page

The browser does not execute scheduling logic. It only sends requests and receives rendered HTML.

### Component 2: Django Routing Layer

This includes:

- [backend/smart_scheduler/urls.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/smart_scheduler/urls.py)
- [backend/core/urls.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/urls.py)

This component maps request paths to the appropriate views.

### Component 3: Django View Layer

This is [backend/core/views.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/views.py).

It is the control component of the application.

Responsibilities:

- handle requests
- validate actions
- call forms and scheduler
- query models
- save results
- choose templates

### Component 4: Form Layer

This is [backend/core/forms.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/forms.py).

Responsibilities:

- validate user input
- define user-editable fields
- simplify create/update operations

### Component 5: Model Layer

This is [backend/core/models.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/models.py).

Responsibilities:

- define entity structure
- define relationships
- enforce model-level timetable constraints

### Component 6: Scheduler Component

This is [backend/core/scheduler.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/scheduler.py).

Responsibilities:

- convert batches and subjects into tasks
- assign teacher, room, and timeslot combinations
- avoid conflicts
- return generated entries

### Component 7: Template / Presentation Layer

This includes:

- base layout
- dashboard
- data entry pages
- timetable page
- classroom finder page
- edit page

Responsibilities:

- display forms
- display messages
- render timetable visually

### Component 8: Static Asset Layer

This includes:

- [backend/core/static/css/custom.css](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/core/static/css/custom.css)
- [public/static/css/custom.css](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/public/static/css/custom.css)

Responsibilities:

- visual appearance
- timetable layout styling
- deployment-friendly CSS serving

### Component 9: Database

Locally:

- SQLite database in [backend/db.sqlite3](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/backend/db.sqlite3)

In deployment:

- Neon PostgreSQL

Responsibilities:

- persist teachers
- persist classrooms
- persist subjects
- persist batches
- persist timeslots
- persist timetable rows

### Component 10: Deployment Adapter

This includes:

- [api/index.py](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/api/index.py)
- [vercel.json](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/vercel.json)

Responsibilities:

- allow Vercel to boot Django
- map incoming requests to the Django application

### Legacy Component Still Present

The repository still contains:

- [cpp_engine/scheduler.cpp](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/cpp_engine/scheduler.cpp)
- [cpp_engine/scheduler.exe](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/cpp_engine/scheduler.exe)
- [data/input.json](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/data/input.json)
- [data/output.json](/Users/shram/OneDrive/Desktop/CP/SmartScheduler/data/output.json)

These belong to the older file-based C++ scheduling path.

The deployed web flow does not currently depend on them.

---

## 8. What Is Actually Active vs Legacy

### Active Path

The current live flow is:

- browser
- Vercel
- `api/index.py`
- Django views
- Python scheduler
- Neon database
- HTML templates

### Legacy Path

The older path still present in the codebase is:

- Django view creates `input.json`
- C++ scheduler reads JSON
- C++ scheduler writes `output.json`
- Django loads `output.json`

This path is still represented in helper functions such as:

- `generate_input_json()`
- `run_cpp_engine()`
- `load_output_json()`
- `save_timetable_from_output()`

But timetable generation in the current active web flow is now handled by:

- `generate_timetable_entries()` in the Python scheduler

So the real deployed behavior is the Python path, not the C++ JSON path.

---

## 9. Final Summary

In plain words:

- the class diagram is centered around `Teacher`, `Classroom`, `Subject`, `Batch`, `TimeSlot`, and `Timetable`
- the activity diagram is the user flow from entering data to generating and viewing timetables
- the sequence diagram is the request-response interaction between browser, views, scheduler, and database
- the collaboration diagram is about how views coordinate models, forms, templates, scheduler, and deployment runtime
- the state diagram describes how the timetable moves from missing data, to ready, to generated, to edited
- the component diagram shows the large software blocks: browser, Django, scheduler, templates, database, and Vercel adapter

This explanation is based on the actual inspected code files listed at the top of this document, not a guessed generic design.
