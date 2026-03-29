"""Application settings (environment variables)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str | None = None
    encryption_key: str | None = None
    internal_jwt_secret: str
    internal_jwt_expire_minutes: int = 5
    bff_service_key: str
    api_key_pepper: str
    superadmin_email: str
    cors_origins: str = "http://localhost:3000"

    @field_validator("internal_jwt_expire_minutes")
    @classmethod
    def jwt_ttl_positive(cls, v: int) -> int:
        if v < 1 or v > 60:
            raise ValueError("INTERNAL_JWT_EXPIRE_MINUTES must be between 1 and 60")
        return v

    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_settings_dep() -> Settings:
    """Use with FastAPI Depends(...) — ``get_settings`` is lru_cached."""
    return get_settings()
