from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "RaspZan"
    environment: str = "local"
    debug: bool = True

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/raspzan",
        description="Primary application database URL.",
    )
    legacy_database_url: str | None = Field(
        default=None,
        description="Read-only connection URL for the legacy PostgreSQL database.",
    )
    secret_key: str = "change-me"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
