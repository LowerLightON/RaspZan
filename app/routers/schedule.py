from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.schedule import ScheduleEntry, ScheduleEntryGroup
from app.schemas.schedule import (
    ScheduleConflictRead,
    ScheduleEntryCancel,
    ScheduleEntryCancelResponse,
    ScheduleEntryCreate,
    ScheduleEntryCreateResponse,
    ScheduleEntryHistoryResponse,
    ScheduleEntryRead,
    ScheduleEntryReplace,
    ScheduleEntryReplaceResponse,
    ScheduleEntryUpdate,
    ScheduleEntryUpdateResponse,
    ScheduleHistoryChangeRead,
    ScheduleHistoryEntryRead,
)
from app.services.schedule_entry_service import ScheduleEntryService
from app.services.schedule_history_query_service import ScheduleHistoryQueryService
from app.services.schedule_query_service import ScheduleQueryOptions, ScheduleQueryService

router = APIRouter(prefix="/schedule", tags=["schedule"])


@router.post("/entries", response_model=ScheduleEntryCreateResponse)
def create_schedule_entry(
    payload: ScheduleEntryCreate,
    db: Session = Depends(get_db),
) -> ScheduleEntryCreateResponse:
    entry = ScheduleEntry(
        entry_type=payload.entry_type,
        lesson_date=payload.lesson_date,
        period_number=payload.period_number,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        week_type=payload.week_type,
        title=payload.title,
        notes=payload.notes,
        lesson_plan_item_id=payload.lesson_plan_item_id,
        subject_id=payload.subject_id,
        teacher_id=payload.teacher_id,
        room_id=payload.room_id,
        group_links=[
            ScheduleEntryGroup(study_group_id=group_id)
            for group_id in payload.group_ids
        ],
    )

    result = ScheduleEntryService().create_entry(db, entry)

    return ScheduleEntryCreateResponse(
        id=result.entry.id if result.entry is not None else None,
        created=result.created,
        conflicts=[
            ScheduleConflictRead(
                code=conflict.code,
                message=conflict.message,
                severity=conflict.severity,
                related_entity_id=conflict.related_entity_id,
            )
            for conflict in result.conflicts
        ],
    )


@router.put("/entries/{entry_id}", response_model=ScheduleEntryUpdateResponse)
def update_schedule_entry(
    entry_id: int,
    payload: ScheduleEntryUpdate,
    db: Session = Depends(get_db),
) -> ScheduleEntryUpdateResponse:
    entry = ScheduleEntry(
        entry_type=payload.entry_type,
        lesson_date=payload.lesson_date,
        period_number=payload.period_number,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        week_type=payload.week_type,
        title=payload.title,
        notes=payload.notes,
        lesson_plan_item_id=payload.lesson_plan_item_id,
        subject_id=payload.subject_id,
        teacher_id=payload.teacher_id,
        room_id=payload.room_id,
    )

    result = ScheduleEntryService().update_entry(
        db,
        entry_id,
        entry,
        payload.group_ids,
    )

    return ScheduleEntryUpdateResponse(
        id=result.entry.id if result.entry is not None else None,
        updated=result.updated,
        conflicts=[
            ScheduleConflictRead(
                code=conflict.code,
                message=conflict.message,
                severity=conflict.severity,
                related_entity_id=conflict.related_entity_id,
            )
            for conflict in result.conflicts
        ],
    )


@router.post("/entries/{entry_id}/cancel", response_model=ScheduleEntryCancelResponse)
def cancel_schedule_entry(
    entry_id: int,
    payload: ScheduleEntryCancel,
    db: Session = Depends(get_db),
) -> ScheduleEntryCancelResponse:
    result = ScheduleEntryService().cancel_entry(
        db,
        entry_id,
        reason=payload.reason,
        changed_by_user_id=payload.changed_by_user_id,
    )

    return ScheduleEntryCancelResponse(
        entry_id=result.entry.id if result.entry is not None else None,
        change_id=result.change.id if result.change is not None else None,
        cancelled=result.cancelled,
    )


@router.post("/entries/{entry_id}/replace", response_model=ScheduleEntryReplaceResponse)
def replace_schedule_entry(
    entry_id: int,
    payload: ScheduleEntryReplace,
    db: Session = Depends(get_db),
) -> ScheduleEntryReplaceResponse:
    replacement_entry = ScheduleEntry(
        entry_type=payload.entry_type,
        lesson_date=payload.lesson_date,
        period_number=payload.period_number,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        week_type=payload.week_type,
        title=payload.title,
        notes=payload.notes,
        lesson_plan_item_id=payload.lesson_plan_item_id,
        subject_id=payload.subject_id,
        teacher_id=payload.teacher_id,
        room_id=payload.room_id,
    )

    result = ScheduleEntryService().replace_entry(
        db,
        entry_id,
        replacement_entry,
        payload.group_ids,
        payload.change_type,
        reason=payload.reason,
        changed_by_user_id=payload.changed_by_user_id,
    )

    return ScheduleEntryReplaceResponse(
        original_entry_id=(
            result.original_entry.id if result.original_entry is not None else None
        ),
        replacement_entry_id=(
            result.replacement_entry.id
            if result.replacement_entry is not None
            else None
        ),
        change_id=result.change.id if result.change is not None else None,
        replaced=result.replaced,
        conflicts=[
            ScheduleConflictRead(
                code=conflict.code,
                message=conflict.message,
                severity=conflict.severity,
                related_entity_id=conflict.related_entity_id,
            )
            for conflict in result.conflicts
        ],
    )


def _to_schedule_entry_read(entry: ScheduleEntry) -> ScheduleEntryRead:
    return ScheduleEntryRead(
        id=entry.id,
        entry_type=entry.entry_type,
        lesson_date=entry.lesson_date,
        period_number=entry.period_number,
        starts_at=entry.starts_at,
        ends_at=entry.ends_at,
        week_type=entry.week_type,
        title=entry.title,
        notes=entry.notes,
        lesson_plan_item_id=entry.lesson_plan_item_id,
        subject_id=entry.subject_id,
        teacher_id=entry.teacher_id,
        room_id=entry.room_id,
        group_ids=[link.study_group_id for link in entry.group_links],
    )


def _to_schedule_history_entry_read(entry: ScheduleEntry) -> ScheduleHistoryEntryRead:
    return ScheduleHistoryEntryRead(
        id=entry.id,
        entry_type=entry.entry_type,
        lesson_date=entry.lesson_date,
        period_number=entry.period_number,
        starts_at=entry.starts_at,
        ends_at=entry.ends_at,
        week_type=entry.week_type,
        title=entry.title,
        notes=entry.notes,
        lesson_plan_item_id=entry.lesson_plan_item_id,
        subject_id=entry.subject_id,
        teacher_id=entry.teacher_id,
        room_id=entry.room_id,
        group_ids=[link.study_group_id for link in entry.group_links],
    )


@router.get("/entries/{entry_id}/history", response_model=ScheduleEntryHistoryResponse)
def get_schedule_entry_history(
    entry_id: int,
    db: Session = Depends(get_db),
) -> ScheduleEntryHistoryResponse:
    history = ScheduleHistoryQueryService().get_entry_history(db, entry_id)
    if history is None:
        raise HTTPException(status_code=404, detail="Schedule entry not found")

    return ScheduleEntryHistoryResponse(
        requested_entry_id=history.requested_entry_id,
        root_entry=_to_schedule_history_entry_read(history.root_entry),
        changes=[
            ScheduleHistoryChangeRead(
                id=change.id,
                change_type=change.change_type,
                effective_date=change.effective_date,
                reason=change.reason,
                notes=change.notes,
                changed_by_user_id=change.changed_by_user_id,
                original_entry_id=change.original_entry_id,
                replacement_entry_id=change.replacement_entry_id,
                replacement_entry=(
                    _to_schedule_history_entry_read(change.replacement_entry)
                    if change.replacement_entry is not None
                    else None
                ),
            )
            for change in history.changes
        ],
        truncated=history.truncated,
    )


@router.get("/groups/{group_id}", response_model=list[ScheduleEntryRead])
def get_group_schedule(
    group_id: int,
    date_from: date = Query(...),
    date_to: date = Query(...),
    include_cancelled: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[ScheduleEntryRead]:
    entries = ScheduleQueryService().get_group_schedule(
        db,
        group_id,
        date_from,
        date_to,
        options=ScheduleQueryOptions(include_cancelled=include_cancelled),
    )
    return [_to_schedule_entry_read(entry) for entry in entries]


@router.get("/teachers/{teacher_id}", response_model=list[ScheduleEntryRead])
def get_teacher_schedule(
    teacher_id: int,
    date_from: date = Query(...),
    date_to: date = Query(...),
    include_cancelled: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[ScheduleEntryRead]:
    entries = ScheduleQueryService().get_teacher_schedule(
        db,
        teacher_id,
        date_from,
        date_to,
        options=ScheduleQueryOptions(include_cancelled=include_cancelled),
    )
    return [_to_schedule_entry_read(entry) for entry in entries]


@router.get("/rooms/{room_id}", response_model=list[ScheduleEntryRead])
def get_room_schedule(
    room_id: int,
    date_from: date = Query(...),
    date_to: date = Query(...),
    include_cancelled: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[ScheduleEntryRead]:
    entries = ScheduleQueryService().get_room_schedule(
        db,
        room_id,
        date_from,
        date_to,
        options=ScheduleQueryOptions(include_cancelled=include_cancelled),
    )
    return [_to_schedule_entry_read(entry) for entry in entries]
