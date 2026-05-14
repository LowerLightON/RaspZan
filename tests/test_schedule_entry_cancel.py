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
from app.models.enums import ScheduleChangeType, ScheduleEntryType
from app.models.schedule import ScheduleChange, ScheduleEntry
from app.services.schedule_entry_service import ScheduleEntryService


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


def _entry() -> ScheduleEntry:
    return ScheduleEntry(
        entry_type=ScheduleEntryType.LESSON,
        lesson_date=date(2026, 9, 1),
        period_number=1,
        title="Original lesson",
    )


def test_cancel_existing_entry_creates_schedule_change(db: Session) -> None:
    entry = _entry()
    db.add(entry)
    db.commit()

    result = ScheduleEntryService().cancel_entry(
        db,
        entry.id,
        reason="Teacher unavailable",
    )

    assert result.cancelled is True
    assert result.entry is not None
    assert result.change is not None
    assert result.change.change_type == ScheduleChangeType.CANCELLATION
    assert result.change.original_entry_id == entry.id
    assert result.change.replacement_entry_id is None
    assert result.change.reason == "Teacher unavailable"
    assert result.change.effective_date == entry.lesson_date


def test_cancel_does_not_delete_schedule_entry(db: Session) -> None:
    entry = _entry()
    db.add(entry)
    db.commit()

    ScheduleEntryService().cancel_entry(db, entry.id)

    assert db.get(ScheduleEntry, entry.id) is not None
    assert db.scalar(select(ScheduleChange)) is not None


def test_cancel_missing_entry_returns_cancelled_false(db: Session) -> None:
    result = ScheduleEntryService().cancel_entry(db, 999)

    assert result.cancelled is False
    assert result.entry is None
    assert result.change is None


def test_cancel_api_endpoint_works(client: TestClient, db: Session) -> None:
    entry = _entry()
    db.add(entry)
    db.commit()

    response = client.post(
        f"/schedule/entries/{entry.id}/cancel",
        json={"reason": "Manual cancellation", "changed_by_user_id": None},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["cancelled"] is True
    assert body["entry_id"] == entry.id
    assert body["change_id"] is not None

    change = db.get(ScheduleChange, body["change_id"])
    assert change is not None
    assert change.change_type == ScheduleChangeType.CANCELLATION
