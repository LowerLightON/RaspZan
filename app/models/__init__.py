"""SQLAlchemy models for the new application schema."""

from app.models.classrooms import Building, Room
from app.models.curriculum import LessonPlan, LessonPlanItem, Subject
from app.models.departments import Department, Faculty, Teacher
from app.models.enums import (
    LessonPlanStatus,
    LessonType,
    ScheduleChangeType,
    ScheduleEntryType,
    UserRole,
    WeekType,
)
from app.models.groups import StudyGroup
from app.models.schedule import ScheduleChange, ScheduleEntry, ScheduleEntryGroup
from app.models.users import Role, User

__all__ = [
    "Building",
    "Department",
    "Faculty",
    "LessonPlan",
    "LessonPlanItem",
    "LessonPlanStatus",
    "LessonType",
    "Role",
    "Room",
    "ScheduleChange",
    "ScheduleChangeType",
    "ScheduleEntry",
    "ScheduleEntryGroup",
    "ScheduleEntryType",
    "StudyGroup",
    "Subject",
    "Teacher",
    "User",
    "UserRole",
    "WeekType",
]
