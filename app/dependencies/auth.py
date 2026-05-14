from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.orm import Session, selectinload

from app.core.errors import ForbiddenError, UnauthorizedError
from app.db.session import get_db
from app.models.users import User
from app.services.permissions import PermissionService, ScheduleWritePermissionError


def get_current_user_stub(
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
    db: Session = Depends(get_db),
) -> User:
    if x_user_id is None:
        raise UnauthorizedError(
            code="missing_user_header",
            message="X-User-Id header is required",
        )

    try:
        user_id = int(x_user_id)
    except ValueError as exc:
        raise UnauthorizedError(
            code="invalid_user_header",
            message="X-User-Id header must be an integer",
        ) from exc

    user = db.get(User, user_id, options=(selectinload(User.role),))
    if user is None:
        raise UnauthorizedError(
            code="user_not_found",
            message="User not found",
        )

    return user


def require_schedule_write_user(
    user: User = Depends(get_current_user_stub),
) -> User:
    if not user.is_active:
        raise ForbiddenError(
            code="inactive_user",
            message="User is inactive",
        )

    try:
        PermissionService().require_schedule_write(user)
    except ScheduleWritePermissionError as exc:
        raise ForbiddenError(
            code="schedule_write_forbidden",
            message="User is not allowed to modify schedule",
        ) from exc

    return user
