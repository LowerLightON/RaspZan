from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.curriculum import LessonPlan, LessonPlanItem, Subject
    from app.models.groups import StudyGroup
    from app.models.schedule import ScheduleEntry
    from app.models.users import User


class Faculty(TimestampMixin, Base):
    __tablename__ = "faculties"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

    departments: Mapped[list[Department]] = relationship(back_populates="faculty")
    study_groups: Mapped[list[StudyGroup]] = relationship(back_populates="faculty")


class Department(TimestampMixin, Base):
    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("faculty_id", "code", name="uq_departments_faculty_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(255))

    faculty_id: Mapped[int | None] = mapped_column(ForeignKey("faculties.id"))

    faculty: Mapped[Faculty | None] = relationship(back_populates="departments")
    users: Mapped[list[User]] = relationship(back_populates="department")
    teachers: Mapped[list[Teacher]] = relationship(back_populates="department")
    subjects: Mapped[list[Subject]] = relationship(back_populates="department")
    lesson_plans: Mapped[list[LessonPlan]] = relationship(back_populates="department")


class Teacher(TimestampMixin, Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    last_name: Mapped[str] = mapped_column(String(100))
    first_name: Mapped[str | None] = mapped_column(String(100))
    middle_name: Mapped[str | None] = mapped_column(String(100))
    full_name: Mapped[str] = mapped_column(String(255), index=True)
    position: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)

    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))

    department: Mapped[Department | None] = relationship(back_populates="teachers")
    lesson_plan_items: Mapped[list[LessonPlanItem]] = relationship(
        back_populates="teacher",
    )
    schedule_entries: Mapped[list[ScheduleEntry]] = relationship(
        back_populates="teacher",
    )
