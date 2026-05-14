from enum import StrEnum


class LessonType(StrEnum):
    LECTURE = "lecture"
    PRACTICE = "practice"
    LAB = "lab"
    SEMINAR = "seminar"
    EXAM = "exam"
    CONSULTATION = "consultation"
    OTHER = "other"


class LessonPlanStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class ScheduleEntryType(StrEnum):
    LESSON = "lesson"
    DAY_OFF = "day_off"
    SELF_STUDY = "self_study"


class ScheduleChangeType(StrEnum):
    REPLACEMENT = "replacement"
    MOVE = "move"
    CANCELLATION = "cancellation"


class UserRole(StrEnum):
    ACADEMIC_OFFICE = "academic_office"
    DEPARTMENT = "department"
    SCHEDULER = "scheduler"


class WeekType(StrEnum):
    EVERY = "every"
    ODD = "odd"
    EVEN = "even"
