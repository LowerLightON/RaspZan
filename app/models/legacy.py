from sqlalchemy.orm import Mapped, mapped_column

from app.db.legacy import LegacyBase


class LegacyUser(LegacyBase):
    __tablename__ = "p_secret"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    groups: Mapped[str | None]
    caf: Mapped[str | None]
    who: Mapped[str | None]


class LegacyGroup(LegacyBase):
    __tablename__ = "p_group"

    id: Mapped[int] = mapped_column(primary_key=True)
    groups: Mapped[str]
    sem: Mapped[str]
    facult: Mapped[str]
    specialn: Mapped[str | None]
    v_specialn: Mapped[str | None]
    specializ: Mapped[str | None]


class LegacyDepartment(LegacyBase):
    __tablename__ = "p_caf"

    id: Mapped[int] = mapped_column(primary_key=True)
    caf_code: Mapped[str]
    facult: Mapped[str | None]
    fio: Mapped[str | None]
    pmk: Mapped[str]


class LegacyClassroom(LegacyBase):
    __tablename__ = "p_aud"

    id: Mapped[int] = mapped_column(primary_key=True)
    aud_num: Mapped[str]
    vg: Mapped[str]
    caf: Mapped[str | None]
    vid: Mapped[str | None]
