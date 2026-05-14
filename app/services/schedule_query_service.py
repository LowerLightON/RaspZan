from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.schedule import ScheduleEntry, ScheduleEntryGroup


class ScheduleQueryService:
    def get_group_schedule(
        self,
        db: Session,
        group_id: int,
        date_from: date,
        date_to: date,
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
        return list(db.scalars(statement).unique().all())

    def get_teacher_schedule(
        self,
        db: Session,
        teacher_id: int,
        date_from: date,
        date_to: date,
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
        return list(db.scalars(statement).all())

    def get_room_schedule(
        self,
        db: Session,
        room_id: int,
        date_from: date,
        date_to: date,
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
        return list(db.scalars(statement).all())
