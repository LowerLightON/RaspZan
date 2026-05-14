from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import UserRole
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.departments import Department
    from app.models.schedule import ScheduleChange


class Role(TimestampMixin, Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False),
        unique=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))

    users: Mapped[list[User]] = relationship(back_populates="role")


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    position: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))

    role: Mapped[Role] = relationship(back_populates="users")
    department: Mapped[Department | None] = relationship(back_populates="users")
    schedule_changes: Mapped[list[ScheduleChange]] = relationship(
        back_populates="changed_by",
        foreign_keys="ScheduleChange.changed_by_user_id",
    )
