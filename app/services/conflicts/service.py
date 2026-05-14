from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.models.schedule import ScheduleEntry
from app.services.conflicts.base import BaseConflictValidator
from app.services.conflicts.group_conflict import GroupConflictValidator
from app.services.conflicts.models import ScheduleConflict
from app.services.conflicts.room_conflict import RoomConflictValidator
from app.services.conflicts.teacher_conflict import TeacherConflictValidator


class ScheduleConflictService:
    def __init__(
        self,
        validators: Sequence[BaseConflictValidator] | None = None,
    ) -> None:
        self.validators = list(
            validators
            if validators is not None
            else (
                TeacherConflictValidator(),
                RoomConflictValidator(),
                GroupConflictValidator(),
            )
        )

    def validate_entry(
        self,
        db: Session,
        entry: ScheduleEntry,
        exclude_entry_id: int | None = None,
    ) -> list[ScheduleConflict]:
        conflicts: list[ScheduleConflict] = []

        for validator in self.validators:
            conflicts.extend(
                validator.validate(
                    db,
                    entry,
                    exclude_entry_id=exclude_entry_id,
                )
            )

        return conflicts
