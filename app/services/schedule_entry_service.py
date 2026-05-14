from dataclasses import dataclass

from sqlalchemy.orm import Session, selectinload

from app.models.enums import ScheduleChangeType
from app.models.schedule import ScheduleChange, ScheduleEntry, ScheduleEntryGroup
from app.services.conflicts import ScheduleConflict, ScheduleConflictService


@dataclass(frozen=True)
class CreateScheduleEntryResult:
    entry: ScheduleEntry | None
    conflicts: list[ScheduleConflict]
    created: bool


@dataclass(frozen=True)
class UpdateScheduleEntryResult:
    entry: ScheduleEntry | None
    conflicts: list[ScheduleConflict]
    updated: bool


@dataclass(frozen=True)
class CancelScheduleEntryResult:
    entry: ScheduleEntry | None
    change: ScheduleChange | None
    cancelled: bool


class ScheduleEntryService:
    def __init__(
        self,
        conflict_service: ScheduleConflictService | None = None,
    ) -> None:
        self.conflict_service = conflict_service or ScheduleConflictService()

    def create_entry(
        self,
        db: Session,
        entry: ScheduleEntry,
    ) -> CreateScheduleEntryResult:
        conflicts = self.conflict_service.validate_entry(db, entry)
        has_error_conflicts = any(
            conflict.severity == "error"
            for conflict in conflicts
        )

        if has_error_conflicts:
            return CreateScheduleEntryResult(
                entry=None,
                conflicts=conflicts,
                created=False,
            )

        db.add(entry)
        db.commit()
        db.refresh(entry)

        return CreateScheduleEntryResult(
            entry=entry,
            conflicts=conflicts,
            created=True,
        )

    def update_entry(
        self,
        db: Session,
        entry_id: int,
        entry_data: ScheduleEntry,
        group_ids: list[int],
    ) -> UpdateScheduleEntryResult:
        existing = db.get(
            ScheduleEntry,
            entry_id,
            options=(selectinload(ScheduleEntry.group_links),),
        )

        if existing is None:
            return UpdateScheduleEntryResult(
                entry=None,
                conflicts=[],
                updated=False,
            )

        existing.entry_type = entry_data.entry_type
        existing.lesson_date = entry_data.lesson_date
        existing.period_number = entry_data.period_number
        existing.starts_at = entry_data.starts_at
        existing.ends_at = entry_data.ends_at
        existing.week_type = entry_data.week_type
        existing.title = entry_data.title
        existing.notes = entry_data.notes
        existing.lesson_plan_item_id = entry_data.lesson_plan_item_id
        existing.subject_id = entry_data.subject_id
        existing.teacher_id = entry_data.teacher_id
        existing.room_id = entry_data.room_id
        existing.group_links = [
            ScheduleEntryGroup(study_group_id=group_id)
            for group_id in group_ids
        ]

        conflicts = self.conflict_service.validate_entry(
            db,
            existing,
            exclude_entry_id=entry_id,
        )
        has_error_conflicts = any(
            conflict.severity == "error"
            for conflict in conflicts
        )

        if has_error_conflicts:
            db.rollback()
            return UpdateScheduleEntryResult(
                entry=None,
                conflicts=conflicts,
                updated=False,
            )

        db.commit()
        db.refresh(existing)

        return UpdateScheduleEntryResult(
            entry=existing,
            conflicts=conflicts,
            updated=True,
        )

    def cancel_entry(
        self,
        db: Session,
        entry_id: int,
        reason: str | None = None,
        changed_by_user_id: int | None = None,
    ) -> CancelScheduleEntryResult:
        entry = db.get(ScheduleEntry, entry_id)

        if entry is None:
            return CancelScheduleEntryResult(
                entry=None,
                change=None,
                cancelled=False,
            )

        change = ScheduleChange(
            change_type=ScheduleChangeType.CANCELLATION,
            original_entry_id=entry.id,
            replacement_entry_id=None,
            reason=reason,
            changed_by_user_id=changed_by_user_id,
            effective_date=entry.lesson_date,
        )

        db.add(change)
        db.commit()
        db.refresh(change)
        db.refresh(entry)

        return CancelScheduleEntryResult(
            entry=entry,
            change=change,
            cancelled=True,
        )
