from datetime import date
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.schedule import ScheduleEntry, ScheduleEntryGroup
from app.services.schedule_projection import apply_active_schedule_projection


@dataclass(frozen=True)
class ScheduleQueryOptions:
    include_cancelled: bool = False


@dataclass(frozen=True)
class SchedulePagination:
    limit: int = 20
    offset: int = 0


@dataclass(frozen=True)
class ScheduleEntryFilters:
    subject_id: int | None = None
    teacher_id: int | None = None
    room_id: int | None = None


@dataclass(frozen=True)
class ScheduleQueryPage:
    items: list[ScheduleEntry]
    total: int
    limit: int
    offset: int


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

    def _apply_entry_filters(
        self,
        statement,
        filters: ScheduleEntryFilters | None,
    ):
        if filters is None:
            return statement

        if filters.subject_id is not None:
            statement = statement.where(ScheduleEntry.subject_id == filters.subject_id)
        if filters.teacher_id is not None:
            statement = statement.where(ScheduleEntry.teacher_id == filters.teacher_id)
        if filters.room_id is not None:
            statement = statement.where(ScheduleEntry.room_id == filters.room_id)

        return statement

    def _paginate_schedule_statement(
        self,
        db: Session,
        statement,
        pagination: SchedulePagination,
        *,
        unique_items: bool = False,
    ) -> ScheduleQueryPage:
        count_statement = select(func.count()).select_from(
            statement.order_by(None).subquery()
        )
        total = db.scalar(count_statement) or 0

        items_statement = statement.limit(pagination.limit).offset(pagination.offset)
        result = db.scalars(items_statement)
        items = result.unique().all() if unique_items else result.all()

        return ScheduleQueryPage(
            items=list(items),
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
        )

    def get_group_schedule(
        self,
        db: Session,
        group_id: int,
        date_from: date,
        date_to: date,
        options: ScheduleQueryOptions | None = None,
        filters: ScheduleEntryFilters | None = None,
        pagination: SchedulePagination = SchedulePagination(),
    ) -> ScheduleQueryPage:
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
        statement = self._apply_entry_filters(statement, filters)
        statement = self._apply_query_options(statement, options)
        return self._paginate_schedule_statement(
            db,
            statement,
            pagination,
            unique_items=True,
        )

    def get_teacher_schedule(
        self,
        db: Session,
        teacher_id: int,
        date_from: date,
        date_to: date,
        options: ScheduleQueryOptions | None = None,
        filters: ScheduleEntryFilters | None = None,
        pagination: SchedulePagination = SchedulePagination(),
    ) -> ScheduleQueryPage:
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
        statement = self._apply_entry_filters(statement, filters)
        statement = self._apply_query_options(statement, options)
        return self._paginate_schedule_statement(db, statement, pagination)

    def get_room_schedule(
        self,
        db: Session,
        room_id: int,
        date_from: date,
        date_to: date,
        options: ScheduleQueryOptions | None = None,
        filters: ScheduleEntryFilters | None = None,
        pagination: SchedulePagination = SchedulePagination(),
    ) -> ScheduleQueryPage:
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
        statement = self._apply_entry_filters(statement, filters)
        statement = self._apply_query_options(statement, options)
        return self._paginate_schedule_statement(db, statement, pagination)
