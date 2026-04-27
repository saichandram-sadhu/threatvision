"""Application settings (environment variables)."""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic import AliasChoices, Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str | None = None
    #: Set to ``require`` (or ``true``) for Supabase / hosted Postgres that enforces TLS.
    database_ssl: str | None = None
    encryption_key: str | None = None
    internal_jwt_secret: str
    internal_jwt_expire_minutes: int = 5
    bff_service_key: str
    api_key_pepper: str
    superadmin_email: str
    cors_origins: str = "http://localhost:3000"
    max_request_body_bytes: int = 8_388_608
    gemini_api_key: str | None = None
    #: ``production`` / ``prod`` forces ``dev_quick_admin_login`` off regardless of env var.
    environment: str = Field(default="development", validation_alias=AliasChoices("ENVIRONMENT", "APP_ENV"))
    #: If true, ``POST /auth/login`` accepts email ``admin`` + password ``admin`` (maps to ``admin@threatvision.dev``). Forced off when ``environment`` is production.
    dev_quick_admin_login: bool = False
    #: ``POST /auth/register`` throttle: attempts per UTC hour per client IP (X-Forwarded-For / client).
    register_ip_max_per_hour: int = Field(default=20, ge=1, le=10_000)
    #: ``POST /auth/register`` throttle: attempts per UTC hour per normalized email.
    register_email_max_per_hour: int = Field(default=10, ge=1, le=10_000)
    #: Verify TLS certificates when calling MISP. Set ``false`` for local Docker MISP with self-signed HTTPS.
    misp_tls_verify: bool = True
    #: Optional plaintext fallback when platform_settings ciphertext cannot be decrypted (wrong ENCRYPTION_KEY) or empty.
    platform_misp_url: str | None = None
    platform_misp_api_key: str | None = None

    @field_validator("platform_misp_url", "platform_misp_api_key", mode="before")
    @classmethod
    def strip_optional_platform_misp(cls, v: object) -> str | None:
        if v is None:
            return None
        if isinstance(v, str):
            s = v.strip()
            return s if s else None
        return str(v) if v else None

    @field_validator("dev_quick_admin_login", "misp_tls_verify", mode="before")
    @classmethod
    def coerce_env_bool(cls, v: object) -> bool:
        if isinstance(v, str):
            s = v.strip().lower()
            if s in ("0", "false", "no", "off", ""):
                return False
            if s in ("1", "true", "yes", "on"):
                return True
        return bool(v)

    @field_validator("dev_quick_admin_login", mode="after")
    @classmethod
    def production_disables_dev_quick_admin(cls, v: bool, info: ValidationInfo) -> bool:
        # OS env wins over .env and constructor kwargs (pydantic-settings); deploy sets ENVIRONMENT=production.
        env = (
            os.environ.get("ENVIRONMENT", "").strip().lower()
            or os.environ.get("APP_ENV", "").strip().lower()
            or str(info.data.get("environment") or "").strip().lower()
        )
        if env in ("production", "prod"):
            return False
        return v

    @field_validator("internal_jwt_expire_minutes")
    @classmethod
    def jwt_ttl_positive(cls, v: int) -> int:
        if v < 1 or v > 60:
            raise ValueError("INTERNAL_JWT_EXPIRE_MINUTES must be between 1 and 60")
        return v

    @field_validator("max_request_body_bytes")
    @classmethod
    def body_limit_sane(cls, v: int) -> int:
        if v < 65_536 or v > 100 * 1024 * 1024:
            raise ValueError("MAX_REQUEST_BODY_BYTES must be between 65536 and 104857600")
        return v

    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_settings_dep() -> Settings:
    """Use with FastAPI Depends(...) — ``get_settings`` is lru_cached."""
    return get_settings()
