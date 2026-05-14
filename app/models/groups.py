from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.curriculum import LessonPlan
    from app.models.departments import Faculty
    from app.models.schedule import ScheduleEntry, ScheduleEntryGroup


class StudyGroup(TimestampMixin, Base):
    __tablename__ = "study_groups"
    __table_args__ = (
        UniqueConstraint("faculty_id", "code", name="uq_study_groups_faculty_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    course: Mapped[int | None]
    academic_year: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(default=True)

    faculty_id: Mapped[int | None] = mapped_column(ForeignKey("faculties.id"))
    parent_group_id: Mapped[int | None] = mapped_column(ForeignKey("study_groups.id"))

    faculty: Mapped[Faculty | None] = relationship(back_populates="study_groups")
    parent_group: Mapped[StudyGroup | None] = relationship(
        remote_side=[id],
        back_populates="subgroups",
    )
    subgroups: Mapped[list[StudyGroup]] = relationship(back_populates="parent_group")
    lesson_plans: Mapped[list[LessonPlan]] = relationship(back_populates="study_group")
    schedule_entries: Mapped[list[ScheduleEntry]] = relationship(
        secondary="schedule_entry_groups",
        back_populates="groups",
        overlaps="entry,entry_links,group,group_links",
    )
    schedule_entry_links: Mapped[list[ScheduleEntryGroup]] = relationship(
        back_populates="group",
        overlaps="groups,schedule_entries",
    )
