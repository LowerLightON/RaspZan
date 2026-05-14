from collections.abc import Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.departments import Teacher
from app.models.enums import ScheduleEntryType, UserRole
from app.models.groups import StudyGroup
from app.models.schedule import ScheduleEntry, ScheduleEntryGroup
from app.models.users import Role, User


@pytest.fixture()
def db() -> Iterator[Session]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    with session_factory() as session:
        yield session

    Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db: Session) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "entry_type": "lesson",
        "lesson_date": "2026-09-01",
        "period_number": 1,
        "starts_at": None,
        "ends_at": None,
        "week_type": "every",
        "title": "Updated lesson",
        "notes": None,
        "lesson_plan_item_id": None,
        "subject_id": None,
        "teacher_id": None,
        "room_id": None,
        "group_ids": [],
    }
    payload.update(overrides)
    return payload


def _auth_headers(db: Session, role_code: UserRole = UserRole.SCHEDULER) -> dict[str, str]:
    role = Role(code=role_code, name=role_code.value)
    user = User(
        username=f"{role_code.value}_user",
        password_hash="stub",
        full_name="Schedule Writer",
        role=role,
    )
    db.add(user)
    db.commit()
    return {"X-User-Id": str(user.id)}


def _entry(**overrides: object) -> ScheduleEntry:
    values = {
        "entry_type": ScheduleEntryType.LESSON,
        "lesson_date": date(2026, 9, 1),
        "period_number": 1,
        "title": "Original lesson",
    }
    values.update(overrides)
    return ScheduleEntry(**values)


def test_schedule_entry_update_success(client: TestClient, db: Session) -> None:
    entry = _entry()
    db.add(entry)
    db.commit()

    response = client.put(
        f"/schedule/entries/{entry.id}",
        json=_payload(title="New title", period_number=2),
        headers=_auth_headers(db),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["updated"] is True
    assert body["id"] == entry.id
    assert body["conflicts"] == []

    updated = db.get(ScheduleEntry, entry.id)
    assert updated is not None
    assert updated.title == "New title"
    assert updated.period_number == 2


def test_schedule_entry_update_blocked_by_teacher_conflict(
    client: TestClient,
    db: Session,
) -> None:
    teacher_one = Teacher(last_name="Ivanov", full_name="Ivanov I.I.")
    teacher_two = Teacher(last_name="Petrov", full_name="Petrov P.P.")
    db.add_all([teacher_one, teacher_two])
    db.commit()

    entry = _entry(teacher_id=teacher_one.id)
    conflicting_entry = _entry(teacher_id=teacher_two.id)
    db.add_all([entry, conflicting_entry])
    db.commit()

    response = client.put(
        f"/schedule/entries/{entry.id}",
        json=_payload(teacher_id=teacher_two.id),
        headers=_auth_headers(db),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["updated"] is False
    assert body["id"] is None
    assert body["conflicts"][0]["code"] == "teacher_busy"

    db.expire_all()
    unchanged = db.get(ScheduleEntry, entry.id)
    assert unchanged is not None
    assert unchanged.teacher_id == teacher_one.id


def test_schedule_entry_update_same_slot_does_not_conflict_with_itself(
    client: TestClient,
    db: Session,
) -> None:
    teacher = Teacher(last_name="Ivanov", full_name="Ivanov I.I.")
    db.add(teacher)
    db.commit()

    entry = _entry(teacher_id=teacher.id)
    db.add(entry)
    db.commit()

    response = client.put(
        f"/schedule/entries/{entry.id}",
        json=_payload(teacher_id=teacher.id, title="Same slot update"),
        headers=_auth_headers(db),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["updated"] is True
    assert body["conflicts"] == []


def test_schedule_entry_update_groups(client: TestClient, db: Session) -> None:
    group_one = StudyGroup(code="A-101")
    group_two = StudyGroup(code="B-202")
    db.add_all([group_one, group_two])
    db.commit()

    entry = _entry(
        group_links=[ScheduleEntryGroup(study_group_id=group_one.id)],
    )
    db.add(entry)
    db.commit()

    response = client.put(
        f"/schedule/entries/{entry.id}",
        json=_payload(group_ids=[group_two.id]),
        headers=_auth_headers(db),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["updated"] is True

    group_ids = db.scalars(
        select(ScheduleEntryGroup.study_group_id).where(
            ScheduleEntryGroup.schedule_entry_id == entry.id,
        )
    ).all()
    assert group_ids == [group_two.id]
