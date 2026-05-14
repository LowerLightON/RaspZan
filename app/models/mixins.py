from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class AuditMixin:
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    updated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
