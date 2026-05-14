from datetime import date, time

from pydantic import BaseModel, Field, field_validator

from app.models.enums import ScheduleChangeType, ScheduleEntryType, WeekType


class ScheduleEntryCreate(BaseModel):
    entry_type: ScheduleEntryType
    lesson_date: date
    period_number: int
    starts_at: time | None = None
    ends_at: time | None = None
    week_type: WeekType = WeekType.EVERY
    title: str | None = None
    notes: str | None = None
    lesson_plan_item_id: int | None = None
    subject_id: int | None = None
    teacher_id: int | None = None
    room_id: int | None = None
    group_ids: list[int] = Field(default_factory=list)


class ScheduleConflictRead(BaseModel):
    code: str
    message: str
    severity: str
    related_entity_id: int | None = None


class ScheduleEntryCreateResponse(BaseModel):
    id: int | None = None
    created: bool
    conflicts: list[ScheduleConflictRead]


class ScheduleEntryUpdate(ScheduleEntryCreate):
    pass


class ScheduleEntryUpdateResponse(BaseModel):
    id: int | None = None
    updated: bool
    conflicts: list[ScheduleConflictRead]


class ScheduleEntryCancel(BaseModel):
    reason: str | None = None
    changed_by_user_id: int | None = None


class ScheduleEntryCancelResponse(BaseModel):
    entry_id: int | None = None
    change_id: int | None = None
    cancelled: bool


class ScheduleEntryReplace(ScheduleEntryCreate):
    change_type: ScheduleChangeType
    reason: str | None = None
    changed_by_user_id: int | None = None

    @field_validator("change_type")
    @classmethod
    def validate_change_type(
        cls,
        change_type: ScheduleChangeType,
    ) -> ScheduleChangeType:
        if change_type not in {
            ScheduleChangeType.MOVE,
            ScheduleChangeType.REPLACEMENT,
        }:
            raise ValueError("change_type must be move or replacement")
        return change_type


class ScheduleEntryReplaceResponse(BaseModel):
    original_entry_id: int | None = None
    replacement_entry_id: int | None = None
    change_id: int | None = None
    replaced: bool
    conflicts: list[ScheduleConflictRead]


class ScheduleEntryRead(BaseModel):
    id: int
    entry_type: ScheduleEntryType
    lesson_date: date
    period_number: int
    starts_at: time | None = None
    ends_at: time | None = None
    week_type: WeekType
    title: str | None = None
    notes: str | None = None
    lesson_plan_item_id: int | None = None
    subject_id: int | None = None
    teacher_id: int | None = None
    room_id: int | None = None
    group_ids: list[int] = Field(default_factory=list)
