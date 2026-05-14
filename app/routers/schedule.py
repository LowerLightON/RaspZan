from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api_docs import (
    SCHEDULE_HISTORY_ERROR_RESPONSES,
    SCHEDULE_READ_ERROR_RESPONSES,
    SCHEDULE_WRITE_ERROR_RESPONSES,
)
from app.core.errors import NotFoundError
from app.db.session import get_db
from app.dependencies.auth import require_schedule_write_user
from app.models.schedule import ScheduleEntry, ScheduleEntryGroup
from app.models.users import User
from app.schemas.schedule import (
    ScheduleConflictRead,
    ScheduleEntryCancel,
    ScheduleEntryCancelResponse,
    ScheduleEntryCreate,
    ScheduleEntryCreateResponse,
    ScheduleEntryHistoryResponse,
    ScheduleEntryPage,
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
from app.services.schedule_query_service import (
    ScheduleEntryFilters,
    SchedulePagination,
    ScheduleQueryOptions,
    ScheduleQueryService,
)

router = APIRouter(prefix="/schedule", tags=["schedule"])


@router.post(
    "/entries",
    response_model=ScheduleEntryCreateResponse,
    summary="Create schedule entry",
    description=(
        "Creates a schedule entry for the requested date and participants. "
        "Blocking schedule conflicts are returned in the success response with "
        "`created=false`; they are not reported as HTTP errors."
    ),
    responses=SCHEDULE_WRITE_ERROR_RESPONSES,
)
def create_schedule_entry(
    payload: ScheduleEntryCreate,
    _current_user: User = Depends(require_schedule_write_user),
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


@router.put(
    "/entries/{entry_id}",
    response_model=ScheduleEntryUpdateResponse,
    summary="Update schedule entry",
    description=(
        "Updates an existing schedule entry. Blocking schedule conflicts are "
        "returned in the success response with `updated=false`; they are not "
        "reported as HTTP errors."
    ),
    responses=SCHEDULE_WRITE_ERROR_RESPONSES,
)
def update_schedule_entry(
    entry_id: int,
    payload: ScheduleEntryUpdate,
    _current_user: User = Depends(require_schedule_write_user),
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


@router.post(
    "/entries/{entry_id}/cancel",
    response_model=ScheduleEntryCancelResponse,
    summary="Cancel schedule entry",
    description=(
        "Cancels a schedule entry and records the cancellation in the temporal "
        "schedule change history."
    ),
    responses=SCHEDULE_WRITE_ERROR_RESPONSES,
)
def cancel_schedule_entry(
    entry_id: int,
    payload: ScheduleEntryCancel,
    current_user: User = Depends(require_schedule_write_user),
    db: Session = Depends(get_db),
) -> ScheduleEntryCancelResponse:
    result = ScheduleEntryService().cancel_entry(
        db,
        entry_id,
        reason=payload.reason,
        changed_by_user_id=current_user.id,
    )

    return ScheduleEntryCancelResponse(
        entry_id=result.entry.id if result.entry is not None else None,
        change_id=result.change.id if result.change is not None else None,
        cancelled=result.cancelled,
    )


@router.post(
    "/entries/{entry_id}/replace",
    response_model=ScheduleEntryReplaceResponse,
    summary="Replace or move schedule entry",
    description=(
        "Creates a replacement or moved entry and links it to the original "
        "entry through schedule change history. Blocking conflicts are returned "
        "in the success response with `replaced=false`; they are not reported "
        "as HTTP errors."
    ),
    responses=SCHEDULE_WRITE_ERROR_RESPONSES,
)
def replace_schedule_entry(
    entry_id: int,
    payload: ScheduleEntryReplace,
    current_user: User = Depends(require_schedule_write_user),
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
        changed_by_user_id=current_user.id,
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


@router.get(
    "/entries/{entry_id}/history",
    response_model=ScheduleEntryHistoryResponse,
    summary="Get schedule entry history",
    description=(
        "Returns the root schedule entry and temporal changes related to the "
        "requested entry."
    ),
    responses=SCHEDULE_HISTORY_ERROR_RESPONSES,
)
def get_schedule_entry_history(
    entry_id: int,
    db: Session = Depends(get_db),
) -> ScheduleEntryHistoryResponse:
    history = ScheduleHistoryQueryService().get_entry_history(db, entry_id)
    if history is None:
        raise NotFoundError(
            code="schedule_not_found",
            message="Schedule entry not found",
        )

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


@router.get(
    "/groups/{group_id}",
    response_model=ScheduleEntryPage,
    summary="Get group schedule",
    description=(
        "Returns active schedule entries for a study group within the requested "
        "date range. Cancelled entries are excluded unless requested."
    ),
    responses=SCHEDULE_READ_ERROR_RESPONSES,
)
def get_group_schedule(
    group_id: int,
    date_from: date = Query(...),
    date_to: date = Query(...),
    subject_id: int | None = Query(None),
    teacher_id: int | None = Query(None),
    room_id: int | None = Query(None),
    include_cancelled: bool = Query(default=False),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> ScheduleEntryPage:
    page = ScheduleQueryService().get_group_schedule(
        db,
        group_id,
        date_from,
        date_to,
        options=ScheduleQueryOptions(include_cancelled=include_cancelled),
        filters=ScheduleEntryFilters(
            subject_id=subject_id,
            teacher_id=teacher_id,
            room_id=room_id,
        ),
        pagination=SchedulePagination(limit=limit, offset=offset),
    )
    return ScheduleEntryPage(
        items=[_to_schedule_entry_read(entry) for entry in page.items],
        total=page.total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get(
    "/teachers/{teacher_id}",
    response_model=ScheduleEntryPage,
    summary="Get teacher schedule",
    description=(
        "Returns active schedule entries for a teacher within the requested "
        "date range. Cancelled entries are excluded unless requested."
    ),
    responses=SCHEDULE_READ_ERROR_RESPONSES,
)
def get_teacher_schedule(
    teacher_id: int,
    date_from: date = Query(...),
    date_to: date = Query(...),
    subject_id: int | None = Query(None),
    room_id: int | None = Query(None),
    include_cancelled: bool = Query(default=False),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> ScheduleEntryPage:
    page = ScheduleQueryService().get_teacher_schedule(
        db,
        teacher_id,
        date_from,
        date_to,
        options=ScheduleQueryOptions(include_cancelled=include_cancelled),
        filters=ScheduleEntryFilters(
            subject_id=subject_id,
            room_id=room_id,
        ),
        pagination=SchedulePagination(limit=limit, offset=offset),
    )
    return ScheduleEntryPage(
        items=[_to_schedule_entry_read(entry) for entry in page.items],
        total=page.total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get(
    "/rooms/{room_id}",
    response_model=ScheduleEntryPage,
    summary="Get room schedule",
    description=(
        "Returns active schedule entries for a room within the requested date "
        "range. Cancelled entries are excluded unless requested."
    ),
    responses=SCHEDULE_READ_ERROR_RESPONSES,
)
def get_room_schedule(
    room_id: int,
    date_from: date = Query(...),
    date_to: date = Query(...),
    subject_id: int | None = Query(None),
    teacher_id: int | None = Query(None),
    include_cancelled: bool = Query(default=False),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> ScheduleEntryPage:
    page = ScheduleQueryService().get_room_schedule(
        db,
        room_id,
        date_from,
        date_to,
        options=ScheduleQueryOptions(include_cancelled=include_cancelled),
        filters=ScheduleEntryFilters(
            subject_id=subject_id,
            teacher_id=teacher_id,
        ),
        pagination=SchedulePagination(limit=limit, offset=offset),
    )
    return ScheduleEntryPage(
        items=[_to_schedule_entry_read(entry) for entry in page.items],
        total=page.total,
        limit=page.limit,
        offset=page.offset,
    )
