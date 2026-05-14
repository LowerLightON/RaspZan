"""Seed demo schedule data for visual Schedule Explorer checks.

Run:
    python -m app.scripts.seed_demo_schedule
"""

from collections.abc import Callable
from datetime import date, time
from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.models
from app.db.session import SessionLocal
from app.models.classrooms import Building, Room
from app.models.curriculum import Subject
from app.models.departments import Department, Faculty, Teacher
from app.models.enums import ScheduleEntryType, UserRole, WeekType
from app.models.groups import StudyGroup
from app.models.schedule import ScheduleEntry
from app.models.users import Role, User

ModelT = TypeVar("ModelT")

DEMO_NOTE = "seed_demo_schedule"
DEMO_PASSWORD_HASH = "todo-password-hash-not-plain-text"


def get_or_create(
    db: Session,
    model: type[ModelT],
    lookup: dict[str, object],
    defaults: dict[str, object] | None = None,
) -> ModelT:
    statement = select(model)
    for field_name, value in lookup.items():
        statement = statement.where(getattr(model, field_name) == value)

    existing = db.scalar(statement.limit(1))
    if existing is not None:
        return existing

    instance = model(**lookup, **(defaults or {}))
    db.add(instance)
    db.flush()
    return instance


def apply_values(instance: object, values: dict[str, object]) -> None:
    for field_name, value in values.items():
        setattr(instance, field_name, value)


def seed_base_entities(db: Session) -> tuple[
    User,
    StudyGroup,
    dict[str, Teacher],
    dict[str, Room],
    dict[str, Subject],
]:
    role_defaults = {"name": "Планировщик расписания"}
    role = get_or_create(
        db,
        Role,
        {"code": UserRole.SCHEDULER},
        role_defaults,
    )
    apply_values(role, role_defaults)

    faculty_defaults = {"name": "Тестовый факультет"}
    faculty = get_or_create(
        db,
        Faculty,
        {"code": "DEV-FAC"},
        faculty_defaults,
    )
    apply_values(faculty, faculty_defaults)

    department_defaults = {"name": "Тестовая кафедра"}
    department = get_or_create(
        db,
        Department,
        {"faculty_id": faculty.id, "code": "DEV-DEPT"},
        department_defaults,
    )
    apply_values(department, department_defaults)

    planner_defaults = {
        "password_hash": DEMO_PASSWORD_HASH,
        "full_name": "Тестовый планировщик",
        "position": "Планировщик расписания",
        "role_id": role.id,
        "department_id": department.id,
    }
    planner = get_or_create(
        db,
        User,
        {"username": "planner"},
        planner_defaults,
    )
    apply_values(planner, planner_defaults)

    group_defaults = {
        "name": "DEV-101",
        "course": 1,
        "academic_year": "2026/2027",
        "is_active": True,
    }
    group = get_or_create(
        db,
        StudyGroup,
        {"faculty_id": faculty.id, "code": "DEV-101"},
        group_defaults,
    )
    apply_values(group, group_defaults)

    teacher_specs = {
        "ivanov": (
            {"full_name": "Иванов Иван Иванович"},
            {
                "last_name": "Иванов",
                "first_name": "Иван",
                "middle_name": "Иванович",
                "position": "Преподаватель",
                "department_id": department.id,
                "is_active": True,
            },
        ),
        "petrov": (
            {"full_name": "Петров Петр Петрович"},
            {
                "last_name": "Петров",
                "first_name": "Петр",
                "middle_name": "Петрович",
                "position": "Преподаватель",
                "department_id": department.id,
                "is_active": True,
            },
        ),
    }
    teachers = {}
    for key, (lookup, defaults) in teacher_specs.items():
        teachers[key] = get_or_create(db, Teacher, lookup, defaults)
        apply_values(teachers[key], defaults)

    building_defaults = {
        "name": "Тестовый корпус",
        "campus": "Тестовый городок",
        "address": "Тестовый адрес",
    }
    building = get_or_create(
        db,
        Building,
        {"code": "DEV-BLD"},
        building_defaults,
    )
    apply_values(building, building_defaults)

    room_specs = {
        "101": (
            {"building_id": building.id, "number": "101"},
            {
                "name": "Аудитория 101",
                "capacity": 30,
                "room_type": "lecture",
                "is_active": True,
            },
        ),
        "202": (
            {"building_id": building.id, "number": "202"},
            {
                "name": "Аудитория 202",
                "capacity": 24,
                "room_type": "lab",
                "is_active": True,
            },
        ),
    }
    rooms = {}
    for key, (lookup, defaults) in room_specs.items():
        rooms[key] = get_or_create(db, Room, lookup, defaults)
        apply_values(rooms[key], defaults)

    subject_specs = {
        "math": (
            {"department_id": department.id, "code": "DEV-MATH"},
            {
                "name": "Тестовая математика",
                "short_name": "Математика",
                "created_by_user_id": planner.id,
                "updated_by_user_id": planner.id,
            },
        ),
        "physics": (
            {"department_id": department.id, "code": "DEV-PHYS"},
            {
                "name": "Тестовая физика",
                "short_name": "Физика",
                "created_by_user_id": planner.id,
                "updated_by_user_id": planner.id,
            },
        ),
        "informatics": (
            {"department_id": department.id, "code": "DEV-INFO"},
            {
                "name": "Тестовая информатика",
                "short_name": "Информатика",
                "created_by_user_id": planner.id,
                "updated_by_user_id": planner.id,
            },
        ),
    }
    subjects = {}
    for key, (lookup, defaults) in subject_specs.items():
        subjects[key] = get_or_create(db, Subject, lookup, defaults)
        apply_values(subjects[key], defaults)

    return planner, group, teachers, rooms, subjects


def get_or_create_schedule_entry(
    db: Session,
    *,
    group: StudyGroup,
    planner: User,
    subject: Subject,
    teacher: Teacher,
    room: Room,
    lesson_date: date,
    period_number: int,
    starts_at: time,
    ends_at: time,
    title: str,
) -> ScheduleEntry:
    existing = db.scalar(
        select(ScheduleEntry)
        .where(ScheduleEntry.notes == DEMO_NOTE)
        .where(ScheduleEntry.lesson_date == lesson_date)
        .where(ScheduleEntry.period_number == period_number)
        .where(ScheduleEntry.subject_id == subject.id)
        .where(ScheduleEntry.teacher_id == teacher.id)
        .where(ScheduleEntry.room_id == room.id)
        .where(ScheduleEntry.title == title)
        .limit(1)
    )

    if existing is not None:
        if group not in existing.groups:
            existing.groups.append(group)
        return existing

    entry = ScheduleEntry(
        entry_type=ScheduleEntryType.LESSON,
        lesson_date=lesson_date,
        period_number=period_number,
        starts_at=starts_at,
        ends_at=ends_at,
        week_type=WeekType.EVERY,
        title=title,
        notes=DEMO_NOTE,
        subject_id=subject.id,
        teacher_id=teacher.id,
        room_id=room.id,
        groups=[group],
        created_by_user_id=planner.id,
        updated_by_user_id=planner.id,
    )
    db.add(entry)
    db.flush()
    return entry


def seed_demo_schedule(db: Session) -> None:
    planner, group, teachers, rooms, subjects = seed_base_entities(db)

    demo_entries = [
        (
            date(2026, 5, 4),
            1,
            time(9, 0),
            time(10, 30),
            "Тестовая математика",
            subjects["math"],
            teachers["ivanov"],
            rooms["101"],
        ),
        (
            date(2026, 5, 4),
            1,
            time(9, 0),
            time(10, 30),
            "Тестовая физика",
            subjects["physics"],
            teachers["petrov"],
            rooms["202"],
        ),
        (
            date(2026, 5, 5),
            2,
            time(10, 40),
            time(12, 10),
            "Тестовая информатика",
            subjects["informatics"],
            teachers["ivanov"],
            rooms["202"],
        ),
        (
            date(2026, 5, 6),
            3,
            time(12, 40),
            time(14, 10),
            "Тестовая физика",
            subjects["physics"],
            teachers["petrov"],
            rooms["101"],
        ),
        (
            date(2026, 5, 7),
            4,
            time(14, 20),
            time(15, 50),
            "Тестовая математика",
            subjects["math"],
            teachers["ivanov"],
            rooms["101"],
        ),
        (
            date(2026, 5, 8),
            2,
            time(10, 40),
            time(12, 10),
            "Тестовая информатика",
            subjects["informatics"],
            teachers["petrov"],
            rooms["202"],
        ),
        (
            date(2026, 5, 9),
            3,
            time(12, 40),
            time(14, 10),
            "Тестовая математика",
            subjects["math"],
            teachers["ivanov"],
            rooms["202"],
        ),
    ]

    for (
        lesson_date,
        period_number,
        starts_at,
        ends_at,
        title,
        subject,
        teacher,
        room,
    ) in demo_entries:
        get_or_create_schedule_entry(
            db,
            group=group,
            planner=planner,
            subject=subject,
            teacher=teacher,
            room=room,
            lesson_date=lesson_date,
            period_number=period_number,
            starts_at=starts_at,
            ends_at=ends_at,
            title=title,
        )


def main(session_factory: Callable[[], Session] = SessionLocal) -> None:
    with session_factory() as db:
        seed_demo_schedule(db)
        db.commit()


if __name__ == "__main__":
    main()
