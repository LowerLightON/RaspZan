from collections.abc import Iterator
from datetime import date

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.db.base import Base
from app.models.departments import Teacher
from app.models.enums import ScheduleEntryType
from app.models.schedule import ScheduleEntry
from app.services.conflicts import ScheduleConflict
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


class WarningConflictService:
    def validate_entry(
        self,
        db: Session,
        entry: ScheduleEntry,
        exclude_entry_id: int | None = None,
    ) -> list[ScheduleConflict]:
        return [
            ScheduleConflict(
                code="soft_warning",
                message="This warning should not block creation.",
                severity="warning",
                related_entity_id=None,
            )
        ]


def _entry(*, teacher_id: int | None = None) -> ScheduleEntry:
    return ScheduleEntry(
        entry_type=ScheduleEntryType.LESSON,
        lesson_date=date(2026, 9, 1),
        period_number=1,
        teacher_id=teacher_id,
    )


def test_entry_creates_successfully_when_no_conflicts(db: Session) -> None:
    result = ScheduleEntryService().create_entry(db, _entry())

    assert result.created is True
    assert result.entry is not None
    assert result.entry.id is not None
    assert result.conflicts == []
    assert db.scalar(select(ScheduleEntry).where(ScheduleEntry.id == result.entry.id))


def test_entry_is_not_created_when_teacher_conflict_exists(db: Session) -> None:
    teacher = Teacher(last_name="Ivanov", full_name="Ivanov I.I.")
    db.add(teacher)
    db.commit()

    db.add(_entry(teacher_id=teacher.id))
    db.commit()

    result = ScheduleEntryService().create_entry(db, _entry(teacher_id=teacher.id))

    assert result.created is False
    assert result.entry is None
    assert [conflict.code for conflict in result.conflicts] == ["teacher_busy"]
    assert len(db.scalars(select(ScheduleEntry)).all()) == 1


def test_warning_conflict_does_not_block_creation(db: Session) -> None:
    result = ScheduleEntryService(
        conflict_service=WarningConflictService(),
    ).create_entry(db, _entry())

    assert result.created is True
    assert result.entry is not None
    assert result.entry.id is not None
    assert [conflict.severity for conflict in result.conflicts] == ["warning"]
