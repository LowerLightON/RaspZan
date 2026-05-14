"""Seed development data for the new RaspZan database.

Run:
    python -m app.scripts.seed_dev
"""

from collections.abc import Callable
from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.models
from app.db.session import SessionLocal
from app.models.classrooms import Building, Room
from app.models.curriculum import LessonPlan, LessonPlanItem, Subject
from app.models.departments import Department, Faculty, Teacher
from app.models.enums import LessonPlanStatus, LessonType, UserRole
from app.models.groups import StudyGroup
from app.models.users import Role, User

ModelT = TypeVar("ModelT")

# TODO: Replace with real password hashing when authentication is implemented.
DEV_PLANNER_PASSWORD_HASH = "todo-password-hash-not-plain-text"


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


def seed_roles(db: Session) -> dict[UserRole, Role]:
    role_names = {
        UserRole.ACADEMIC_OFFICE: "Учебно-методический отдел",
        UserRole.DEPARTMENT: "Кафедра",
        UserRole.SCHEDULER: "Планировщик расписания",
    }
    return {
        role_code: get_or_create(
            db,
            Role,
            {"code": role_code},
            {"name": role_name},
        )
        for role_code, role_name in role_names.items()
    }


def seed_dev_data(db: Session) -> None:
    roles = seed_roles(db)

    faculty = get_or_create(
        db,
        Faculty,
        {"code": "DEV-FAC"},
        {"name": "Тестовый факультет"},
    )
    department = get_or_create(
        db,
        Department,
        {
            "faculty_id": faculty.id,
            "code": "DEV-DEPT",
        },
        {"name": "Тестовая кафедра"},
    )
    planner = get_or_create(
        db,
        User,
        {"username": "planner"},
        {
            "password_hash": DEV_PLANNER_PASSWORD_HASH,
            "full_name": "Тестовый планировщик",
            "position": "Планировщик расписания",
            "role_id": roles[UserRole.SCHEDULER].id,
            "department_id": department.id,
        },
    )
    group = get_or_create(
        db,
        StudyGroup,
        {
            "faculty_id": faculty.id,
            "code": "DEV-101",
        },
        {
            "name": "DEV-101",
            "course": 1,
            "academic_year": "2026/2027",
        },
    )
    teacher = get_or_create(
        db,
        Teacher,
        {"full_name": "Иванов Иван Иванович"},
        {
            "last_name": "Иванов",
            "first_name": "Иван",
            "middle_name": "Иванович",
            "position": "Преподаватель",
            "department_id": department.id,
        },
    )
    building = get_or_create(
        db,
        Building,
        {"code": "DEV-BLD"},
        {
            "name": "Тестовый корпус",
            "campus": "Тестовый городок",
            "address": "Тестовый адрес",
        },
    )
    get_or_create(
        db,
        Room,
        {
            "building_id": building.id,
            "number": "101",
        },
        {
            "name": "Аудитория 101",
            "capacity": 30,
            "room_type": "lecture",
        },
    )
    subject = get_or_create(
        db,
        Subject,
        {
            "department_id": department.id,
            "code": "DEV-MATH",
        },
        {
            "name": "Тестовая математика",
            "short_name": "Мат.",
            "created_by_user_id": planner.id,
            "updated_by_user_id": planner.id,
        },
    )
    lesson_plan = get_or_create(
        db,
        LessonPlan,
        {
            "subject_id": subject.id,
            "academic_year": "2026/2027",
            "semester": 1,
        },
        {
            "title": "Тестовая СЛС",
            "status": LessonPlanStatus.DRAFT,
            "department_id": department.id,
            "study_group_id": group.id,
            "created_by_user_id": planner.id,
            "updated_by_user_id": planner.id,
        },
    )
    get_or_create(
        db,
        LessonPlanItem,
        {
            "lesson_plan_id": lesson_plan.id,
            "lesson_number": 1,
        },
        {
            "topic": "Вводное занятие",
            "hours": 2,
            "lesson_type": LessonType.LECTURE,
            "teacher_id": teacher.id,
            "created_by_user_id": planner.id,
            "updated_by_user_id": planner.id,
        },
    )


def main(session_factory: Callable[[], Session] = SessionLocal) -> None:
    with session_factory() as db:
        seed_dev_data(db)
        db.commit()


if __name__ == "__main__":
    main()
