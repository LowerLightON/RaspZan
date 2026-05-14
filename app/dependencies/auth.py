from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.users import User
from app.services.permissions import PermissionService, ScheduleWritePermissionError


def get_current_user_stub(
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
    db: Session = Depends(get_db),
) -> User:
    if x_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-Id header is required",
        )

    try:
        user_id = int(x_user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid X-User-Id header",
        ) from exc

    user = db.get(User, user_id, options=(selectinload(User.role),))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


def require_schedule_write_user(
    user: User = Depends(get_current_user_stub),
) -> User:
    try:
        PermissionService().require_schedule_write(user)
    except ScheduleWritePermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User cannot write schedule",
        ) from exc

    return user
