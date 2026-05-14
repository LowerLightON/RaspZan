from app.models.enums import UserRole
from app.models.users import User


class ScheduleWritePermissionError(PermissionError):
    pass


class PermissionService:
    schedule_writer_roles = {
        UserRole.ACADEMIC_OFFICE,
        UserRole.SCHEDULER,
    }

    def can_write_schedule(self, user: User) -> bool:
        if not user.is_active:
            return False

        return user.role.code in self.schedule_writer_roles

    def require_schedule_write(self, user: User) -> None:
        if not self.can_write_schedule(user):
            raise ScheduleWritePermissionError("User cannot write schedule")
