from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.schedule import ScheduleEntry, ScheduleEntryGroup
from app.services.conflicts.base import BaseConflictValidator
from app.services.conflicts.models import ScheduleConflict


class GroupConflictValidator(BaseConflictValidator):
    def validate(
        self,
        db: Session,
        entry: ScheduleEntry,
    ) -> list[ScheduleConflict]:
        group_ids = {group.id for group in entry.groups if group.id is not None}
        group_ids.update(
            link.study_group_id
            for link in entry.group_links
            if link.study_group_id is not None
        )

        if not group_ids:
            return []

        statement = (
            select(ScheduleEntryGroup.study_group_id)
            .join(ScheduleEntry, ScheduleEntry.id == ScheduleEntryGroup.schedule_entry_id)
            .where(
                ScheduleEntry.lesson_date == entry.lesson_date,
                ScheduleEntry.period_number == entry.period_number,
                ScheduleEntryGroup.study_group_id.in_(group_ids),
            )
        )

        if entry.id is not None:
            statement = statement.where(ScheduleEntry.id != entry.id)

        with db.no_autoflush:
            conflict_group_id = db.scalar(statement.limit(1))

        if conflict_group_id is None:
            return []

        return [
            ScheduleConflict(
                code="group_busy",
                message="Study group already has a schedule entry in this time slot.",
                severity="error",
                related_entity_id=conflict_group_id,
            )
        ]
