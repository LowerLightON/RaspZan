from datetime import date
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.schedule import ScheduleEntry, ScheduleEntryGroup
from app.services.schedule_projection import apply_active_schedule_projection


@dataclass(frozen=True)
class ScheduleQueryOptions:
    include_cancelled: bool = False


class ScheduleQueryService:
    def _options(self, options: ScheduleQueryOptions | None) -> ScheduleQueryOptions:
        return options or ScheduleQueryOptions()

    def _apply_active_projection(
        self,
        statement,
        *,
        include_cancelled: bool,
    ):
        return apply_active_schedule_projection(
            statement,
            include_cancelled=include_cancelled,
        )

    def _apply_query_options(self, statement, options: ScheduleQueryOptions | None):
        resolved_options = self._options(options)

        return self._apply_active_projection(
            statement,
            include_cancelled=resolved_options.include_cancelled,
        )

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
