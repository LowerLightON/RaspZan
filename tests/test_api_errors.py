from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import UserRole
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
        full_name="API Error Test User",
        is_active=is_active,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_schedule_write_without_user_header_returns_error_envelope(
    client: TestClient,
) -> None:
    response = client.post("/schedule/entries", json=_payload())

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "missing_user_header"


def test_schedule_write_with_invalid_user_header_returns_error_envelope(
    client: TestClient,
) -> None:
    response = client.post(
        "/schedule/entries",
        json=_payload(),
        headers={"X-User-Id": "abc"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_user_header"


def test_schedule_write_with_unknown_user_returns_error_envelope(
    client: TestClient,
) -> None:
    response = client.post(
        "/schedule/entries",
        json=_payload(),
        headers={"X-User-Id": "999"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "user_not_found"


def test_schedule_write_with_forbidden_role_returns_error_envelope(
    client: TestClient,
    db: Session,
) -> None:
    user = _user(db, role_code=UserRole.DEPARTMENT)

    response = client.post(
        "/schedule/entries",
        json=_payload(),
        headers={"X-User-Id": str(user.id)},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "schedule_write_forbidden"


def test_missing_history_entry_returns_error_envelope(
    client: TestClient,
) -> None:
    response = client.get("/schedule/entries/999/history")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "schedule_not_found"


def test_validation_error_returns_error_envelope(
    client: TestClient,
    db: Session,
) -> None:
    user = _user(db, role_code=UserRole.SCHEDULER)
    payload = _payload()
    del payload["entry_type"]

    response = client.post(
        "/schedule/entries",
        json=payload,
        headers={"X-User-Id": str(user.id)},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert isinstance(body["error"]["details"]["errors"], list)
