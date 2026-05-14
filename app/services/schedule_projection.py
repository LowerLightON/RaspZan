from sqlalchemy import select

from app.models.enums import ScheduleChangeType
from app.models.schedule import ScheduleChange, ScheduleEntry


def inactive_schedule_change_types(
    *,
    include_cancelled: bool = False,
) -> tuple[ScheduleChangeType, ...]:
    change_types = (
        ScheduleChangeType.MOVE,
        ScheduleChangeType.REPLACEMENT,
    )
    if not include_cancelled:
        change_types = (
            ScheduleChangeType.CANCELLATION,
            *change_types,
        )

    return change_types


def superseded_schedule_entry_exists(
    change_types: tuple[ScheduleChangeType, ...],
):
    return (
        select(ScheduleChange.id)
        .where(
            ScheduleChange.original_entry_id == ScheduleEntry.id,
            ScheduleChange.change_type.in_(change_types),
        )
        .exists()
    )


def apply_active_schedule_projection(
    statement,
    *,
    include_cancelled: bool = False,
):
    return statement.where(
        ~superseded_schedule_entry_exists(
            inactive_schedule_change_types(include_cancelled=include_cancelled)
        )
    )
