from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import LessonPlanStatus, LessonType
from app.models.mixins import AuditMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.departments import Department, Teacher
    from app.models.groups import StudyGroup
    from app.models.schedule import ScheduleEntry


class Subject(AuditMixin, TimestampMixin, Base):
    __tablename__ = "subjects"
    __table_args__ = (
        UniqueConstraint("department_id", "code", name="uq_subjects_department_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str | None] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(500), index=True)
    short_name: Mapped[str | None] = mapped_column(String(100))

    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))

    department: Mapped[Department | None] = relationship(back_populates="subjects")
    lesson_plans: Mapped[list[LessonPlan]] = relationship(back_populates="subject")
    schedule_entries: Mapped[list[ScheduleEntry]] = relationship(
        back_populates="subject",
    )


class LessonPlan(AuditMixin, TimestampMixin, Base):
    __tablename__ = "lesson_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    academic_year: Mapped[str] = mapped_column(String(20), index=True)
    semester: Mapped[int]
    title: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[LessonPlanStatus] = mapped_column(
        Enum(LessonPlanStatus, name="lesson_plan_status", native_enum=False),
        default=LessonPlanStatus.DRAFT,
    )
    is_approved: Mapped[bool] = mapped_column(default=False)

    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    study_group_id: Mapped[int | None] = mapped_column(ForeignKey("study_groups.id"))

    subject: Mapped[Subject] = relationship(back_populates="lesson_plans")
    department: Mapped[Department | None] = relationship(back_populates="lesson_plans")
    study_group: Mapped[StudyGroup | None] = relationship(back_populates="lesson_plans")
    items: Mapped[list[LessonPlanItem]] = relationship(
        back_populates="lesson_plan",
        cascade="all, delete-orphan",
    )


class LessonPlanItem(AuditMixin, TimestampMixin, Base):
    __tablename__ = "lesson_plan_items"
    __table_args__ = (
        UniqueConstraint(
            "lesson_plan_id",
            "lesson_number",
            name="uq_lesson_plan_items_plan_number",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_number: Mapped[int]
    topic: Mapped[str] = mapped_column(Text)
    hours: Mapped[int]
    lesson_type: Mapped[LessonType] = mapped_column(
        Enum(LessonType, name="lesson_type", native_enum=False),
    )
    notes: Mapped[str | None] = mapped_column(Text)

    lesson_plan_id: Mapped[int] = mapped_column(ForeignKey("lesson_plans.id"))
    teacher_id: Mapped[int | None] = mapped_column(ForeignKey("teachers.id"))

    lesson_plan: Mapped[LessonPlan] = relationship(back_populates="items")
    teacher: Mapped[Teacher | None] = relationship(back_populates="lesson_plan_items")
    schedule_entries: Mapped[list[ScheduleEntry]] = relationship(
        back_populates="lesson_plan_item",
    )
