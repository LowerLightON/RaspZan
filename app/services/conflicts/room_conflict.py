from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.schedule import ScheduleEntry
from app.services.conflicts.base import BaseConflictValidator
from app.services.conflicts.models import ScheduleConflict


class RoomConflictValidator(BaseConflictValidator):
    def validate(
        self,
        db: Session,
        entry: ScheduleEntry,
    ) -> list[ScheduleConflict]:
        if entry.room_id is None:
            return []

        statement = select(ScheduleEntry.id).where(
            ScheduleEntry.room_id == entry.room_id,
            ScheduleEntry.lesson_date == entry.lesson_date,
            ScheduleEntry.period_number == entry.period_number,
        )

        if entry.id is not None:
            statement = statement.where(ScheduleEntry.id != entry.id)

        with db.no_autoflush:
            conflict_entry_id = db.scalar(statement.limit(1))

        if conflict_entry_id is None:
            return []

        return [
            ScheduleConflict(
                code="room_busy",
                message="Room already has a schedule entry in this time slot.",
                severity="error",
                related_entity_id=entry.room_id,
            )
        ]
