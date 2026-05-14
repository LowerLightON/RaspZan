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
from app.models.classrooms import Room
from app.models.departments import Teacher
from app.models.enums import ScheduleChangeType, ScheduleEntryType
from app.models.groups import StudyGroup
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


def _seed_schedule(db: Session) -> tuple[StudyGroup, Teacher, Room, ScheduleEntry]:
    group = StudyGroup(code="A-101")
    teacher = Teacher(last_name="Ivanov", full_name="Ivanov I.I.")
    room = Room(number="101")
    db.add_all([group, teacher, room])
    db.commit()

    matching_entry = ScheduleEntry(
        entry_type=ScheduleEntryType.LESSON,
        lesson_date=date(2026, 9, 1),
        period_number=1,
        teacher_id=teacher.id,
        room_id=room.id,
        groups=[group],
        title="Math",
    )
    outside_range_entry = ScheduleEntry(
        entry_type=ScheduleEntryType.LESSON,
        lesson_date=date(2026, 10, 1),
        period_number=1,
        teacher_id=teacher.id,
        room_id=room.id,
        groups=[group],
        title="Later Math",
    )
    db.add_all([matching_entry, outside_range_entry])
    db.commit()

    return group, teacher, room, matching_entry


def test_get_group_schedule(client: TestClient, db: Session) -> None:
    group, _, _, entry = _seed_schedule(db)

    response = client.get(
        f"/schedule/groups/{group.id}",
        params={"date_from": "2026-09-01", "date_to": "2026-09-30"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert [item["id"] for item in body["items"]] == [entry.id]
    assert body["items"][0]["group_ids"] == [group.id]


def test_get_teacher_schedule(client: TestClient, db: Session) -> None:
    _, teacher, _, entry = _seed_schedule(db)

    response = client.get(
        f"/schedule/teachers/{teacher.id}",
        params={"date_from": "2026-09-01", "date_to": "2026-09-30"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert [item["id"] for item in body["items"]] == [entry.id]
    assert body["items"][0]["teacher_id"] == teacher.id


def test_get_room_schedule(client: TestClient, db: Session) -> None:
    _, _, room, entry = _seed_schedule(db)

    response = client.get(
        f"/schedule/rooms/{room.id}",
        params={"date_from": "2026-09-01", "date_to": "2026-09-30"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert [item["id"] for item in body["items"]] == [entry.id]
    assert body["items"][0]["room_id"] == room.id


def test_get_teacher_schedule_hides_cancelled_by_default(
    client: TestClient,
    db: Session,
) -> None:
    _, teacher, _, entry = _seed_schedule(db)
    db.add(
        ScheduleChange(
            change_type=ScheduleChangeType.CANCELLATION,
            original_entry_id=entry.id,
            effective_date=entry.lesson_date,
        )
    )
    db.commit()

    response = client.get(
        f"/schedule/teachers/{teacher.id}",
        params={"date_from": "2026-09-01", "date_to": "2026-09-30"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["limit"] == 20
    assert body["offset"] == 0


def test_get_teacher_schedule_can_include_cancelled(
    client: TestClient,
    db: Session,
) -> None:
    _, teacher, _, entry = _seed_schedule(db)
    db.add(
        ScheduleChange(
            change_type=ScheduleChangeType.CANCELLATION,
            original_entry_id=entry.id,
            effective_date=entry.lesson_date,
        )
    )
    db.commit()

    response = client.get(
        f"/schedule/teachers/{teacher.id}",
        params={
            "date_from": "2026-09-01",
            "date_to": "2026-09-30",
            "include_cancelled": "true",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert [item["id"] for item in body["items"]] == [entry.id]


def test_get_teacher_schedule_hides_replaced_original_and_shows_replacement(
    client: TestClient,
    db: Session,
) -> None:
    group, teacher, room, original = _seed_schedule(db)
    replacement = ScheduleEntry(
        entry_type=ScheduleEntryType.LESSON,
        lesson_date=date(2026, 9, 2),
        period_number=2,
        teacher_id=teacher.id,
        room_id=room.id,
        groups=[group],
        title="Replacement Math",
    )
    db.add(replacement)
    db.commit()
    db.add(
        ScheduleChange(
            change_type=ScheduleChangeType.REPLACEMENT,
            original_entry_id=original.id,
            replacement_entry_id=replacement.id,
            effective_date=replacement.lesson_date,
        )
    )
    db.commit()

    response = client.get(
        f"/schedule/teachers/{teacher.id}",
        params={"date_from": "2026-09-01", "date_to": "2026-09-30"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert [item["id"] for item in body["items"]] == [replacement.id]


def test_get_teacher_schedule_hides_moved_original_and_shows_replacement(
    client: TestClient,
    db: Session,
) -> None:
    group, teacher, room, original = _seed_schedule(db)
    moved_entry = ScheduleEntry(
        entry_type=ScheduleEntryType.LESSON,
        lesson_date=date(2026, 9, 3),
        period_number=3,
        teacher_id=teacher.id,
        room_id=room.id,
        groups=[group],
        title="Moved Math",
    )
    db.add(moved_entry)
    db.commit()
    db.add(
        ScheduleChange(
            change_type=ScheduleChangeType.MOVE,
            original_entry_id=original.id,
            replacement_entry_id=moved_entry.id,
            effective_date=original.lesson_date,
        )
    )
    db.commit()

    response = client.get(
        f"/schedule/teachers/{teacher.id}",
        params={"date_from": "2026-09-01", "date_to": "2026-09-30"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert [item["id"] for item in body["items"]] == [moved_entry.id]


def test_get_teacher_schedule_include_cancelled_does_not_show_replaced_original(
    client: TestClient,
    db: Session,
) -> None:
    group, teacher, room, original = _seed_schedule(db)
    replacement = ScheduleEntry(
        entry_type=ScheduleEntryType.LESSON,
        lesson_date=date(2026, 9, 2),
        period_number=2,
        teacher_id=teacher.id,
        room_id=room.id,
        groups=[group],
        title="Replacement Math",
    )
    db.add(replacement)
    db.commit()
    db.add(
        ScheduleChange(
            change_type=ScheduleChangeType.REPLACEMENT,
            original_entry_id=original.id,
            replacement_entry_id=replacement.id,
            effective_date=replacement.lesson_date,
        )
    )
    db.commit()

    response = client.get(
        f"/schedule/teachers/{teacher.id}",
        params={
            "date_from": "2026-09-01",
            "date_to": "2026-09-30",
            "include_cancelled": "true",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert [item["id"] for item in body["items"]] == [replacement.id]


def test_get_teacher_schedule_returns_limited_window(
    client: TestClient,
    db: Session,
) -> None:
    group = StudyGroup(code="A-101")
    teacher = Teacher(last_name="Ivanov", full_name="Ivanov I.I.")
    room = Room(number="101")
    db.add_all([group, teacher, room])
    db.commit()

    entries = [
        ScheduleEntry(
            entry_type=ScheduleEntryType.LESSON,
            lesson_date=date(2026, 9, 1),
            period_number=period_number,
            teacher_id=teacher.id,
            room_id=room.id,
            groups=[group],
            title=f"Math {period_number}",
        )
        for period_number in (1, 2, 3)
    ]
    db.add_all(entries)
    db.commit()

    response = client.get(
        f"/schedule/teachers/{teacher.id}",
        params={
            "date_from": "2026-09-01",
            "date_to": "2026-09-30",
            "limit": "2",
            "offset": "1",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body["items"]] == [
        entries[1].id,
        entries[2].id,
    ]
    assert body["total"] == 3
    assert body["limit"] == 2
    assert body["offset"] == 1


def test_get_teacher_schedule_total_respects_active_projection(
    client: TestClient,
    db: Session,
) -> None:
    _, teacher, _, entry = _seed_schedule(db)
    db.add(
        ScheduleChange(
            change_type=ScheduleChangeType.CANCELLATION,
            original_entry_id=entry.id,
            effective_date=entry.lesson_date,
        )
    )
    db.commit()

    response = client.get(
        f"/schedule/teachers/{teacher.id}",
        params={"date_from": "2026-09-01", "date_to": "2026-09-30"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0


def test_get_teacher_schedule_rejects_invalid_limit(
    client: TestClient,
    db: Session,
) -> None:
    _, teacher, _, _ = _seed_schedule(db)

    response = client.get(
        f"/schedule/teachers/{teacher.id}",
        params={
            "date_from": "2026-09-01",
            "date_to": "2026-09-30",
            "limit": "0",
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert isinstance(body["error"]["details"]["errors"], list)
