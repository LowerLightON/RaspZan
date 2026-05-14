from dataclasses import dataclass


@dataclass(frozen=True)
class ScheduleConflict:
    code: str
    message: str
    severity: str
    related_entity_id: int | None = None
