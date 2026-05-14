from collections.abc import Iterator
from datetime import date

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.db.base import Base
from app.models.departments import Teacher
from app.models.enums import ScheduleChangeType, ScheduleEntryType
from app.models.schedule import ScheduleChange, ScheduleEntry
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


class ErrorConflictService:
    def validate_entry(
        self,
        db: Session,
        entry: ScheduleEntry,
        exclude_entry_id: int | None = None,
    ) -> list[ScheduleConflict]:
        return [
            ScheduleConflict(
                code="hard_conflict",
                message="This conflict should block replacement.",
                severity="error",
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


def test_replace_entry_creates_replacement_and_schedule_change(db: Session) -> None:
    original = _entry()
    db.add(original)
    db.commit()

    replacement = ScheduleEntry(
        entry_type=ScheduleEntryType.LESSON,
        lesson_date=date(2026, 9, 2),
        period_number=2,
        title="Replacement lesson",
    )

    result = ScheduleEntryService().replace_entry(
        db,
        original.id,
        replacement,
        group_ids=[],
        change_type=ScheduleChangeType.MOVE,
        reason="Teacher unavailable",
    )

    assert result.replaced is True
    assert result.original_entry is not None
    assert result.replacement_entry is not None
    assert result.change is not None
    assert result.replacement_entry.id != original.id
    assert result.change.change_type == ScheduleChangeType.MOVE
    assert result.change.original_entry_id == original.id
    assert result.change.replacement_entry_id == result.replacement_entry.id
    assert result.change.reason == "Teacher unavailable"
    assert result.change.effective_date == original.lesson_date


def test_replace_entry_rolls_back_when_error_conflict_exists(db: Session) -> None:
    original = _entry()
    db.add(original)
    db.commit()

    replacement = ScheduleEntry(
        entry_type=ScheduleEntryType.LESSON,
        lesson_date=date(2026, 9, 2),
        period_number=2,
    )

    result = ScheduleEntryService(
        conflict_service=ErrorConflictService(),
    ).replace_entry(
        db,
        original.id,
        replacement,
        group_ids=[],
        change_type=ScheduleChangeType.REPLACEMENT,
    )

    assert result.replaced is False
    assert result.replacement_entry is None
    assert [conflict.code for conflict in result.conflicts] == ["hard_conflict"]
    assert len(db.scalars(select(ScheduleEntry)).all()) == 1
    assert db.scalar(select(ScheduleChange)) is None
