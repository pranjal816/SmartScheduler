from collections import defaultdict


DAY_ORDER = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]


def generate_timetable_entries(batches, classrooms, timeslots):
    batch_busy = {batch.id: set() for batch in batches}
    teacher_busy = defaultdict(set)
    room_busy = defaultdict(set)
    batch_day_load = {batch.id: defaultdict(int) for batch in batches}
    subject_day_load = defaultdict(set)
    room_load = defaultdict(int)
    teacher_load = defaultdict(int)
    timetable = []

    slot_lookup = {slot.id: slot for slot in timeslots}

    tasks = []
    for batch in batches:
        assigned_subjects = list(batch.subjects.prefetch_related("teachers").all())
        for subject in assigned_subjects:
            for _ in range(subject.lectures_per_week):
                tasks.append(
                    {
                        "batch": batch,
                        "subject": subject,
                        "teacher_candidates": list(subject.teachers.all()),
                    }
                )

    tasks.sort(
        key=lambda task: (
            -task["subject"].lectures_per_week,
            len(task["teacher_candidates"]),
            task["batch"].year,
            task["subject"].name,
        )
    )

    for task in tasks:
        batch = task["batch"]
        subject = task["subject"]
        teachers = task["teacher_candidates"]

        best_choice = None
        best_score = None

        for timeslot in timeslots:
            if timeslot.id in batch_busy[batch.id]:
                continue

            day_rank = DAY_ORDER.index(timeslot.day) if timeslot.day in DAY_ORDER else 99
            repeated_same_day = timeslot.day in subject_day_load[(batch.id, subject.id)]

            for teacher in teachers:
                if timeslot.id in teacher_busy[teacher.id]:
                    continue

                for classroom in classrooms:
                    if timeslot.id in room_busy[classroom.id]:
                        continue

                    score = (
                        batch_day_load[batch.id][timeslot.day],
                        1 if repeated_same_day else 0,
                        teacher_load[teacher.id],
                        room_load[classroom.id],
                        day_rank,
                        timeslot.start_time,
                        classroom.capacity,
                    )

                    if best_score is None or score < best_score:
                        best_score = score
                        best_choice = (timeslot, teacher, classroom)

        if best_choice is None:
            return []

        timeslot, teacher, classroom = best_choice
        timetable.append(
            {
                "batch": batch,
                "subject": subject,
                "teacher": teacher,
                "classroom": classroom,
                "timeslot": timeslot,
            }
        )

        batch_busy[batch.id].add(timeslot.id)
        teacher_busy[teacher.id].add(timeslot.id)
        room_busy[classroom.id].add(timeslot.id)
        batch_day_load[batch.id][timeslot.day] += 1
        subject_day_load[(batch.id, subject.id)].add(timeslot.day)
        teacher_load[teacher.id] += 1
        room_load[classroom.id] += 1

    return timetable
