from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.classrooms import Room
from app.models.curriculum import Subject
from app.models.departments import Teacher
from app.models.groups import StudyGroup


class LookupQueryService:
    def list_groups(self, db: Session) -> list[StudyGroup]:
        return list(
            db.scalars(
                select(StudyGroup)
                .where(StudyGroup.is_active.is_(True))
                .order_by(StudyGroup.code),
            ),
        )

    def list_teachers(self, db: Session) -> list[Teacher]:
        return list(
            db.scalars(
                select(Teacher)
                .where(Teacher.is_active.is_(True))
                .order_by(Teacher.full_name),
            ),
        )

    def list_rooms(self, db: Session) -> list[Room]:
        return list(
            db.scalars(
                select(Room).where(Room.is_active.is_(True)).order_by(Room.number),
            ),
        )

    def list_subjects(self, db: Session) -> list[Subject]:
        return list(db.scalars(select(Subject).order_by(Subject.name)))
