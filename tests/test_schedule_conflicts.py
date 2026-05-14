from collections.abc import Iterator
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.db.base import Base
from app.models.classrooms import Room
from app.models.departments import Teacher
from app.models.enums import ScheduleEntryType
from app.models.groups import StudyGroup
from app.models.schedule import ScheduleEntry
from app.services.conflicts import (
    GroupConflictValidator,
    RoomConflictValidator,
    ScheduleConflictService,
    TeacherConflictValidator,
)


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


def _entry(
    *,
    teacher_id: int | None = None,
    room_id: int | None = None,
    groups: list[StudyGroup] | None = None,
) -> ScheduleEntry:
    entry = ScheduleEntry(
        entry_type=ScheduleEntryType.LESSON,
        lesson_date=date(2026, 9, 1),
        period_number=1,
        teacher_id=teacher_id,
        room_id=room_id,
    )
    if groups:
        entry.groups = groups
    return entry


def test_teacher_conflict(db: Session) -> None:
    teacher = Teacher(last_name="Ivanov", full_name="Ivanov I.I.")
    db.add(teacher)
    db.commit()

    db.add(_entry(teacher_id=teacher.id))
    db.commit()

    conflicts = TeacherConflictValidator().validate(
        db,
        _entry(teacher_id=teacher.id),
    )

    assert [conflict.code for conflict in conflicts] == ["teacher_busy"]
    assert conflicts[0].related_entity_id == teacher.id


def test_room_conflict(db: Session) -> None:
    room = Room(number="101")
    db.add(room)
    db.commit()

    db.add(_entry(room_id=room.id))
    db.commit()

    conflicts = RoomConflictValidator().validate(
        db,
        _entry(room_id=room.id),
    )

    assert [conflict.code for conflict in conflicts] == ["room_busy"]
    assert conflicts[0].related_entity_id == room.id


def test_group_conflict(db: Session) -> None:
    group = StudyGroup(code="A-101")
    db.add(group)
    db.commit()

    db.add(_entry(groups=[group]))
    db.commit()

    conflicts = GroupConflictValidator().validate(
        db,
        _entry(groups=[group]),
    )

    assert [conflict.code for conflict in conflicts] == ["group_busy"]
    assert conflicts[0].related_entity_id == group.id


def test_conflict_service_runs_all_validators(db: Session) -> None:
    teacher = Teacher(last_name="Ivanov", full_name="Ivanov I.I.")
    room = Room(number="101")
    group = StudyGroup(code="A-101")
    db.add_all([teacher, room, group])
    db.commit()

    db.add(_entry(teacher_id=teacher.id, room_id=room.id, groups=[group]))
    db.commit()

    conflicts = ScheduleConflictService().validate_entry(
        db,
        _entry(teacher_id=teacher.id, room_id=room.id, groups=[group]),
    )

    assert {conflict.code for conflict in conflicts} == {
        "group_busy",
        "room_busy",
        "teacher_busy",
    }
