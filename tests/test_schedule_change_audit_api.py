from collections.abc import Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import ScheduleEntryType, UserRole
from app.models.schedule import ScheduleChange, ScheduleEntry
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


def _entry(**overrides: object) -> ScheduleEntry:
    values = {
        "entry_type": ScheduleEntryType.LESSON,
        "lesson_date": date(2026, 9, 1),
        "period_number": 1,
        "title": "Math",
    }
    values.update(overrides)
    return ScheduleEntry(**values)


def _persist_entry(db: Session, entry: ScheduleEntry) -> ScheduleEntry:
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def _replace_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "entry_type": "lesson",
        "lesson_date": "2026-09-02",
        "period_number": 2,
        "starts_at": None,
        "ends_at": None,
        "week_type": "every",
        "title": "Replacement Math",
        "notes": None,
        "lesson_plan_item_id": None,
        "subject_id": None,
        "teacher_id": None,
        "room_id": None,
        "group_ids": [],
        "change_type": "replacement",
        "reason": "Teacher unavailable",
        "changed_by_user_id": None,
    }
    payload.update(overrides)
    return payload


def _scheduler_user(db: Session) -> User:
    role = Role(code=UserRole.SCHEDULER, name=UserRole.SCHEDULER.value)
    user = User(
        username="scheduler_audit_user",
        password_hash="stub",
        full_name="Schedule Writer",
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _auth_headers(user: User) -> dict[str, str]:
    return {"X-User-Id": str(user.id)}


def test_cancel_endpoint_sets_changed_by_user_id(
    client: TestClient,
    db: Session,
) -> None:
    user = _scheduler_user(db)
    entry = _persist_entry(db, _entry())

    response = client.post(
        f"/schedule/entries/{entry.id}/cancel",
        json={"reason": "Manual cancellation", "changed_by_user_id": None},
        headers=_auth_headers(user),
    )

    assert response.status_code == 200
    change = db.get(ScheduleChange, response.json()["change_id"])
    assert change is not None
    assert change.changed_by_user_id == user.id


def test_replace_endpoint_sets_changed_by_user_id(
    client: TestClient,
    db: Session,
) -> None:
    user = _scheduler_user(db)
    original = _persist_entry(db, _entry())

    response = client.post(
        f"/schedule/entries/{original.id}/replace",
        json=_replace_payload(),
        headers=_auth_headers(user),
    )

    assert response.status_code == 200
    change = db.get(ScheduleChange, response.json()["change_id"])
    assert change is not None
    assert change.changed_by_user_id == user.id


def test_history_returns_changed_by_user_id_for_cancel_change(
    client: TestClient,
    db: Session,
) -> None:
    user = _scheduler_user(db)
    entry = _persist_entry(db, _entry())

    client.post(
        f"/schedule/entries/{entry.id}/cancel",
        json={"reason": "Manual cancellation", "changed_by_user_id": None},
        headers=_auth_headers(user),
    )

    response = client.get(f"/schedule/entries/{entry.id}/history")

    assert response.status_code == 200
    assert response.json()["changes"][0]["changed_by_user_id"] == user.id


def test_history_returns_changed_by_user_id_for_replace_change(
    client: TestClient,
    db: Session,
) -> None:
    user = _scheduler_user(db)
    original = _persist_entry(db, _entry())

    replace_response = client.post(
        f"/schedule/entries/{original.id}/replace",
        json=_replace_payload(),
        headers=_auth_headers(user),
    )

    response = client.get(f"/schedule/entries/{original.id}/history")

    assert replace_response.status_code == 200
    assert response.status_code == 200
    assert response.json()["changes"][0]["changed_by_user_id"] == user.id
