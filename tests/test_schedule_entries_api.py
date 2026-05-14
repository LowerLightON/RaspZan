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
from app.models.enums import ScheduleEntryType
from app.models.schedule import ScheduleEntry


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
        "title": "Math",
        "notes": None,
        "lesson_plan_item_id": None,
        "subject_id": None,
        "teacher_id": None,
        "room_id": None,
        "group_ids": [],
    }
    payload.update(overrides)
    return payload


def test_schedule_entry_create_success(client: TestClient, db: Session) -> None:
    response = client.post("/schedule/entries", json=_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["created"] is True
    assert body["id"] is not None
    assert body["conflicts"] == []

    entry = db.scalar(select(ScheduleEntry).where(ScheduleEntry.id == body["id"]))
    assert entry is not None
    assert entry.entry_type == ScheduleEntryType.LESSON


def test_schedule_entry_create_blocked_by_teacher_conflict(
    client: TestClient,
    db: Session,
) -> None:
    teacher = Teacher(last_name="Ivanov", full_name="Ivanov I.I.")
    db.add(teacher)
    db.commit()

    db.add(
        ScheduleEntry(
            entry_type=ScheduleEntryType.LESSON,
            lesson_date=date(2026, 9, 1),
            period_number=1,
            teacher_id=teacher.id,
        )
    )
    db.commit()

    response = client.post(
        "/schedule/entries",
        json=_payload(teacher_id=teacher.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["created"] is False
    assert body["id"] is None
    assert body["conflicts"]
    assert body["conflicts"][0]["code"] == "teacher_busy"
    assert body["conflicts"][0]["severity"] == "error"
    assert len(db.scalars(select(ScheduleEntry)).all()) == 1
