# SmartScheduler

SmartScheduler is a Django + C++ timetable generation project for managing teachers, classrooms, subjects, batches, and time slots, then generating a conflict-free timetable using a native scheduling engine.

## Project Structure

- `backend/`: Django application, templates, and SQLite database.
- `cpp_engine/`: C++ scheduling engine source and optional compiled executable.
- `data/`: JSON handoff files between Django and the C++ engine.

## Run The Project

1. Create and activate a Python virtual environment.
2. Install Django:

```bash
pip install django
```

3. Apply migrations:

```bash
cd backend
python manage.py migrate
```

4. Compile the C++ engine if `scheduler.exe` is not present:

```bash
cd ../cpp_engine
g++ -std=c++17 -O2 -I. scheduler.cpp -o scheduler.exe
```

5. Start the Django server:

```bash
cd ../backend
python manage.py runserver
```

## Notes

- `json.hpp` should be placed in `cpp_engine/` before compiling.
- The engine reads `data/input.json` and writes `data/output.json`.
- Lab subjects are scheduled as consecutive slots.
