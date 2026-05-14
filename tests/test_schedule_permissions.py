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
from app.models.groups import StudyGroup
from app.models.schedule import ScheduleEntry
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


def _entry(**overrides: object) -> ScheduleEntry:
    values = {
        "entry_type": ScheduleEntryType.LESSON,
        "lesson_date": date(2026, 9, 1),
        "period_number": 1,
        "title": "Math",
    }
    values.update(overrides)
    return ScheduleEntry(**values)


def _user(
    db: Session,
    *,
    role_code: UserRole,
    is_active: bool = True,
) -> User:
    role = Role(code=role_code, name=role_code.value)
    user = User(
        username=f"{role_code.value}_{is_active}",
        password_hash="stub",
        full_name="Permission Test User",
        is_active=is_active,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _auth_headers(user: User) -> dict[str, str]:
    return {"X-User-Id": str(user.id)}


def test_schedule_write_without_user_header_returns_401(
    client: TestClient,
) -> None:
    response = client.post("/schedule/entries", json=_payload())

    assert response.status_code == 401


def test_schedule_write_with_unknown_user_returns_401(
    client: TestClient,
) -> None:
    response = client.post(
        "/schedule/entries",
        json=_payload(),
        headers={"X-User-Id": "999"},
    )

    assert response.status_code == 401


def test_inactive_user_cannot_create_schedule_entry(
    client: TestClient,
    db: Session,
) -> None:
    user = _user(db, role_code=UserRole.SCHEDULER, is_active=False)

    response = client.post(
        "/schedule/entries",
        json=_payload(),
        headers=_auth_headers(user),
    )

    assert response.status_code == 403


def test_department_user_cannot_create_schedule_entry(
    client: TestClient,
    db: Session,
) -> None:
    user = _user(db, role_code=UserRole.DEPARTMENT)

    response = client.post(
        "/schedule/entries",
        json=_payload(),
        headers=_auth_headers(user),
    )

    assert response.status_code == 403


def test_scheduler_user_can_create_schedule_entry(
    client: TestClient,
    db: Session,
) -> None:
    user = _user(db, role_code=UserRole.SCHEDULER)

    response = client.post(
        "/schedule/entries",
        json=_payload(),
        headers=_auth_headers(user),
    )

    assert response.status_code == 200
    assert response.json()["created"] is True


def test_academic_office_user_can_create_schedule_entry(
    client: TestClient,
    db: Session,
) -> None:
    user = _user(db, role_code=UserRole.ACADEMIC_OFFICE)

    response = client.post(
        "/schedule/entries",
        json=_payload(),
        headers=_auth_headers(user),
    )

    assert response.status_code == 200
    assert response.json()["created"] is True


def test_read_group_schedule_works_without_user_header(
    client: TestClient,
    db: Session,
) -> None:
    group = StudyGroup(code="A-101")
    entry = _entry(groups=[group])
    db.add(entry)
    db.commit()

    response = client.get(
        f"/schedule/groups/{group.id}",
        params={"date_from": "2026-09-01", "date_to": "2026-09-30"},
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [entry.id]


def test_history_endpoint_works_without_user_header(
    client: TestClient,
    db: Session,
) -> None:
    entry = _entry()
    db.add(entry)
    db.commit()

    response = client.get(f"/schedule/entries/{entry.id}/history")

    assert response.status_code == 200
    assert response.json()["root_entry"]["id"] == entry.id
