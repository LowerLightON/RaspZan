from datetime import date
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import ScheduleChangeType
from app.models.schedule import ScheduleChange, ScheduleEntry, ScheduleEntryGroup


@dataclass(frozen=True)
class ScheduleQueryOptions:
    include_cancelled: bool = False


class ScheduleQueryService:
    def _options(self, options: ScheduleQueryOptions | None) -> ScheduleQueryOptions:
        return options or ScheduleQueryOptions()

    def _apply_query_options(self, statement, options: ScheduleQueryOptions | None):
        resolved_options = self._options(options)

        if resolved_options.include_cancelled:
            return statement

        cancellation_exists = (
            select(ScheduleChange.id)
            .where(
                ScheduleChange.original_entry_id == ScheduleEntry.id,
                ScheduleChange.change_type == ScheduleChangeType.CANCELLATION,
            )
            .exists()
        )
        return statement.where(~cancellation_exists)

    def get_group_schedule(
        self,
        db: Session,
        group_id: int,
        date_from: date,
        date_to: date,
        options: ScheduleQueryOptions | None = None,
    ) -> list[ScheduleEntry]:
        statement = (
            select(ScheduleEntry)
            .join(
                ScheduleEntryGroup,
                ScheduleEntryGroup.schedule_entry_id == ScheduleEntry.id,
            )
            .where(
                ScheduleEntryGroup.study_group_id == group_id,
                ScheduleEntry.lesson_date >= date_from,
                ScheduleEntry.lesson_date <= date_to,
            )
            .options(selectinload(ScheduleEntry.group_links))
            .order_by(ScheduleEntry.lesson_date, ScheduleEntry.period_number)
        )
        statement = self._apply_query_options(statement, options)
        return list(db.scalars(statement).unique().all())

    def get_teacher_schedule(
        self,
        db: Session,
        teacher_id: int,
        date_from: date,
        date_to: date,
        options: ScheduleQueryOptions | None = None,
    ) -> list[ScheduleEntry]:
        statement = (
            select(ScheduleEntry)
            .where(
                ScheduleEntry.teacher_id == teacher_id,
                ScheduleEntry.lesson_date >= date_from,
                ScheduleEntry.lesson_date <= date_to,
            )
            .options(selectinload(ScheduleEntry.group_links))
            .order_by(ScheduleEntry.lesson_date, ScheduleEntry.period_number)
        )
        statement = self._apply_query_options(statement, options)
        return list(db.scalars(statement).all())

    def get_room_schedule(
        self,
        db: Session,
        room_id: int,
        date_from: date,
        date_to: date,
        options: ScheduleQueryOptions | None = None,
    ) -> list[ScheduleEntry]:
        statement = (
            select(ScheduleEntry)
            .where(
                ScheduleEntry.room_id == room_id,
                ScheduleEntry.lesson_date >= date_from,
                ScheduleEntry.lesson_date <= date_to,
            )
            .options(selectinload(ScheduleEntry.group_links))
            .order_by(ScheduleEntry.lesson_date, ScheduleEntry.period_number)
        )
        statement = self._apply_query_options(statement, options)
        return list(db.scalars(statement).all())
