from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.classrooms import Room
from app.models.curriculum import Subject
from app.models.departments import Teacher
from app.models.groups import StudyGroup
from app.schemas.lookup import (
    GroupLookupItem,
    RoomLookupItem,
    SubjectLookupItem,
    TeacherLookupItem,
)
from app.services.lookup_query_service import LookupQueryService

router = APIRouter(prefix="/lookup", tags=["lookup"])


def _group_item(group: StudyGroup) -> GroupLookupItem:
    return GroupLookupItem(id=group.id, label=group.code, code=group.code)


def _teacher_item(teacher: Teacher) -> TeacherLookupItem:
    return TeacherLookupItem(
        id=teacher.id,
        label=teacher.full_name,
        full_name=teacher.full_name,
    )


def _room_item(room: Room) -> RoomLookupItem:
    return RoomLookupItem(id=room.id, label=room.number, number=room.number)


def _subject_item(subject: Subject) -> SubjectLookupItem:
    return SubjectLookupItem(id=subject.id, label=subject.name, name=subject.name)


@router.get(
    "/groups",
    response_model=list[GroupLookupItem],
    summary="List group lookup items",
    description="Returns active study groups for select/dropdown controls.",
)
def list_group_lookup(db: Session = Depends(get_db)) -> list[GroupLookupItem]:
    groups = LookupQueryService().list_groups(db)
    return [_group_item(group) for group in groups]


@router.get(
    "/teachers",
    response_model=list[TeacherLookupItem],
    summary="List teacher lookup items",
    description="Returns active teachers for select/dropdown controls.",
)
def list_teacher_lookup(db: Session = Depends(get_db)) -> list[TeacherLookupItem]:
    teachers = LookupQueryService().list_teachers(db)
    return [_teacher_item(teacher) for teacher in teachers]


@router.get(
    "/rooms",
    response_model=list[RoomLookupItem],
    summary="List room lookup items",
    description="Returns active rooms for select/dropdown controls.",
)
def list_room_lookup(db: Session = Depends(get_db)) -> list[RoomLookupItem]:
    rooms = LookupQueryService().list_rooms(db)
    return [_room_item(room) for room in rooms]


@router.get(
    "/subjects",
    response_model=list[SubjectLookupItem],
    summary="List subject lookup items",
    description="Returns subjects for select/dropdown controls.",
)
def list_subject_lookup(db: Session = Depends(get_db)) -> list[SubjectLookupItem]:
    subjects = LookupQueryService().list_subjects(db)
    return [_subject_item(subject) for subject in subjects]
