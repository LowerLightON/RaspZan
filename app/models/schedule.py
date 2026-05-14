from __future__ import annotations

from datetime import date, time
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ScheduleChangeType, ScheduleEntryType, WeekType
from app.models.mixins import AuditMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.classrooms import Room
    from app.models.curriculum import LessonPlanItem, Subject
    from app.models.departments import Teacher
    from app.models.groups import StudyGroup
    from app.models.users import User


class ScheduleEntry(AuditMixin, TimestampMixin, Base):
    __tablename__ = "schedule_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    entry_type: Mapped[ScheduleEntryType] = mapped_column(
        Enum(ScheduleEntryType, name="schedule_entry_type", native_enum=False),
    )
    lesson_date: Mapped[date] = mapped_column(Date, index=True)
    period_number: Mapped[int] = mapped_column(index=True)
    starts_at: Mapped[time | None] = mapped_column(Time)
    ends_at: Mapped[time | None] = mapped_column(Time)
    week_type: Mapped[WeekType] = mapped_column(
        Enum(WeekType, name="week_type", native_enum=False),
        default=WeekType.EVERY,
    )
    title: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)

    lesson_plan_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("lesson_plan_items.id"),
    )
    subject_id: Mapped[int | None] = mapped_column(ForeignKey("subjects.id"))
    teacher_id: Mapped[int | None] = mapped_column(ForeignKey("teachers.id"))
    room_id: Mapped[int | None] = mapped_column(ForeignKey("rooms.id"))

    groups: Mapped[list[StudyGroup]] = relationship(
        secondary="schedule_entry_groups",
        back_populates="schedule_entries",
        overlaps="entry,entry_links,group,group_links",
    )
    group_links: Mapped[list[ScheduleEntryGroup]] = relationship(
        back_populates="entry",
        cascade="all, delete-orphan",
        overlaps="groups,schedule_entries",
    )
    lesson_plan_item: Mapped[LessonPlanItem | None] = relationship(
        back_populates="schedule_entries",
    )
    subject: Mapped[Subject | None] = relationship(back_populates="schedule_entries")
    teacher: Mapped[Teacher | None] = relationship(back_populates="schedule_entries")
    room: Mapped[Room | None] = relationship(back_populates="schedule_entries")
    changes_from: Mapped[list[ScheduleChange]] = relationship(
        foreign_keys="ScheduleChange.original_entry_id",
        back_populates="original_entry",
    )
    changes_to: Mapped[list[ScheduleChange]] = relationship(
        foreign_keys="ScheduleChange.replacement_entry_id",
        back_populates="replacement_entry",
    )


class ScheduleEntryGroup(TimestampMixin, Base):
    __tablename__ = "schedule_entry_groups"
    __table_args__ = (
        UniqueConstraint(
            "schedule_entry_id",
            "study_group_id",
            name="uq_schedule_entry_groups_entry_group",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    schedule_entry_id: Mapped[int] = mapped_column(ForeignKey("schedule_entries.id"))
    study_group_id: Mapped[int] = mapped_column(ForeignKey("study_groups.id"))

    entry: Mapped[ScheduleEntry] = relationship(
        back_populates="group_links",
        overlaps="groups,schedule_entries",
    )
    group: Mapped[StudyGroup] = relationship(
        back_populates="schedule_entry_links",
        overlaps="groups,schedule_entries",
    )


class ScheduleChange(AuditMixin, TimestampMixin, Base):
    __tablename__ = "schedule_changes"

    id: Mapped[int] = mapped_column(primary_key=True)
    change_type: Mapped[ScheduleChangeType] = mapped_column(
        Enum(ScheduleChangeType, name="schedule_change_type", native_enum=False),
        index=True,
    )
    reason: Mapped[str | None] = mapped_column(Text)
    effective_date: Mapped[date | None] = mapped_column(Date, index=True)
    notes: Mapped[str | None] = mapped_column(Text)

    original_entry_id: Mapped[int] = mapped_column(ForeignKey("schedule_entries.id"))
    replacement_entry_id: Mapped[int | None] = mapped_column(
        ForeignKey("schedule_entries.id"),
    )
    changed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    original_entry: Mapped[ScheduleEntry] = relationship(
        foreign_keys=[original_entry_id],
        back_populates="changes_from",
    )
    replacement_entry: Mapped[ScheduleEntry | None] = relationship(
        foreign_keys=[replacement_entry_id],
        back_populates="changes_to",
    )
    changed_by: Mapped[User | None] = relationship(
        back_populates="schedule_changes",
        foreign_keys=[changed_by_user_id],
    )
