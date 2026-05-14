from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class LegacyBase(DeclarativeBase):
    pass


def _ensure_read_only(statement: str) -> None:
    normalized = statement.lstrip().lower()
    if not normalized.startswith("select"):
        raise RuntimeError("Legacy database access is read-only.")


@lru_cache
def get_legacy_engine() -> Engine:
    if settings.legacy_database_url is None:
        raise RuntimeError("LEGACY_DATABASE_URL is not configured.")

    engine = create_engine(settings.legacy_database_url, pool_pre_ping=True)

    @event.listens_for(engine, "before_cursor_execute")
    def _block_writes(
        conn,
        cursor,
        statement,
        parameters,
        context,
        executemany,
    ) -> None:
        _ensure_read_only(statement)

    return engine


def get_legacy_session_factory() -> sessionmaker[Session]:
    return sessionmaker(
        bind=get_legacy_engine(),
        class_=Session,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def get_legacy_db() -> Generator[Session, None, None]:
    db = get_legacy_session_factory()()
    try:
        yield db
    finally:
        db.close()
