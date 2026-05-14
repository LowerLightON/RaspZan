from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.schedule import ScheduleEntry


class Building(TimestampMixin, Base):
    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    campus: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(String(500))

    rooms: Mapped[list[Room]] = relationship(back_populates="building")


class Room(TimestampMixin, Base):
    __tablename__ = "rooms"
    __table_args__ = (
        UniqueConstraint("building_id", "number", name="uq_rooms_building_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    capacity: Mapped[int | None]
    room_type: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(default=True)

    building_id: Mapped[int | None] = mapped_column(ForeignKey("buildings.id"))

    building: Mapped[Building | None] = relationship(back_populates="rooms")
    schedule_entries: Mapped[list[ScheduleEntry]] = relationship(back_populates="room")
