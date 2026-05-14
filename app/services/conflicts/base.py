from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from app.models.schedule import ScheduleEntry
from app.services.conflicts.models import ScheduleConflict


class BaseConflictValidator(ABC):
    @abstractmethod
    def validate(
        self,
        db: Session,
        entry: ScheduleEntry,
    ) -> list[ScheduleConflict]:
        raise NotImplementedError
