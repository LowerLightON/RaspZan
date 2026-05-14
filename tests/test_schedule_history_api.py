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
from app.models.enums import ScheduleChangeType, ScheduleEntryType
from app.models.schedule import ScheduleChange, ScheduleEntry


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


def _entry(
    *,
    lesson_date: date = date(2026, 9, 1),
    period_number: int = 1,
    title: str = "Math",
) -> ScheduleEntry:
    return ScheduleEntry(
        entry_type=ScheduleEntryType.LESSON,
        lesson_date=lesson_date,
        period_number=period_number,
        title=title,
    )


def _persist_entry(db: Session, entry: ScheduleEntry) -> ScheduleEntry:
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def _add_change(
    db: Session,
    *,
    change_type: ScheduleChangeType,
    original: ScheduleEntry,
    replacement: ScheduleEntry | None = None,
    reason: str | None = None,
) -> ScheduleChange:
    change = ScheduleChange(
        change_type=change_type,
        original_entry_id=original.id,
        replacement_entry_id=replacement.id if replacement is not None else None,
        effective_date=original.lesson_date,
        reason=reason,
        changed_by_user_id=None,
    )
    db.add(change)
    db.commit()
    db.refresh(change)
    return change


def test_entry_without_changes_returns_empty_changes(
    client: TestClient,
    db: Session,
) -> None:
    entry = _persist_entry(db, _entry())

    response = client.get(f"/schedule/entries/{entry.id}/history")

    assert response.status_code == 200
    body = response.json()
    assert body["requested_entry_id"] == entry.id
    assert body["root_entry"]["id"] == entry.id
    assert body["changes"] == []
    assert body["truncated"] is False


def test_cancellation_appears_in_history(client: TestClient, db: Session) -> None:
    entry = _persist_entry(db, _entry())
    change = _add_change(
        db,
        change_type=ScheduleChangeType.CANCELLATION,
        original=entry,
        reason="Teacher unavailable",
    )

    response = client.get(f"/schedule/entries/{entry.id}/history")

    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body["changes"]] == [change.id]
    assert body["changes"][0]["change_type"] == "cancellation"
    assert body["changes"][0]["replacement_entry"] is None
    assert body["changes"][0]["reason"] == "Teacher unavailable"


def test_replacement_includes_replacement_entry(
    client: TestClient,
    db: Session,
) -> None:
    original = _persist_entry(db, _entry())
    replacement = _persist_entry(
        db,
        _entry(
            lesson_date=date(2026, 9, 2),
            period_number=2,
            title="Replacement Math",
        ),
    )
    _add_change(
        db,
        change_type=ScheduleChangeType.REPLACEMENT,
        original=original,
        replacement=replacement,
    )

    response = client.get(f"/schedule/entries/{original.id}/history")

    assert response.status_code == 200
    body = response.json()
    assert body["root_entry"]["id"] == original.id
    assert body["changes"][0]["change_type"] == "replacement"
    assert body["changes"][0]["replacement_entry_id"] == replacement.id
    assert body["changes"][0]["replacement_entry"]["id"] == replacement.id
    assert body["changes"][0]["replacement_entry"]["title"] == "Replacement Math"


def test_move_includes_moved_entry(client: TestClient, db: Session) -> None:
    original = _persist_entry(db, _entry())
    moved_entry = _persist_entry(
        db,
        _entry(
            lesson_date=date(2026, 9, 3),
            period_number=3,
            title="Moved Math",
        ),
    )
    _add_change(
        db,
        change_type=ScheduleChangeType.MOVE,
        original=original,
        replacement=moved_entry,
    )

    response = client.get(f"/schedule/entries/{original.id}/history")

    assert response.status_code == 200
    body = response.json()
    assert body["changes"][0]["change_type"] == "move"
    assert body["changes"][0]["replacement_entry"]["id"] == moved_entry.id
    assert body["changes"][0]["replacement_entry"]["period_number"] == 3


def test_request_by_replacement_entry_returns_full_history_from_root(
    client: TestClient,
    db: Session,
) -> None:
    original = _persist_entry(db, _entry())
    replacement = _persist_entry(
        db,
        _entry(
            lesson_date=date(2026, 9, 2),
            period_number=2,
            title="Replacement Math",
        ),
    )
    change = _add_change(
        db,
        change_type=ScheduleChangeType.REPLACEMENT,
        original=original,
        replacement=replacement,
    )

    response = client.get(f"/schedule/entries/{replacement.id}/history")

    assert response.status_code == 200
    body = response.json()
    assert body["requested_entry_id"] == replacement.id
    assert body["root_entry"]["id"] == original.id
    assert [item["id"] for item in body["changes"]] == [change.id]


def test_cancellation_after_replacement_appears_as_terminal_event(
    client: TestClient,
    db: Session,
) -> None:
    original = _persist_entry(db, _entry())
    replacement = _persist_entry(
        db,
        _entry(
            lesson_date=date(2026, 9, 2),
            period_number=2,
            title="Replacement Math",
        ),
    )
    replacement_change = _add_change(
        db,
        change_type=ScheduleChangeType.REPLACEMENT,
        original=original,
        replacement=replacement,
    )
    cancellation_change = _add_change(
        db,
        change_type=ScheduleChangeType.CANCELLATION,
        original=replacement,
        reason="Cancelled after replacement",
    )

    response = client.get(f"/schedule/entries/{replacement.id}/history")

    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body["changes"]] == [
        replacement_change.id,
        cancellation_change.id,
    ]
    assert body["changes"][1]["change_type"] == "cancellation"
    assert body["changes"][1]["replacement_entry_id"] is None
    assert body["changes"][1]["replacement_entry"] is None
