"""Admin / superadmin API models (M10)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class AdminUserOut(BaseModel):
    userId: str
    email: EmailStr
    role: str
    dailyLimit: int
    unlimited: bool
    banned: bool
    apiKeyPrefix: str | None = None
    createdAt: datetime


class AdminUserPatch(BaseModel):
    dailyLimit: int | None = Field(default=None, ge=1, le=10_000_000)
    unlimited: bool | None = None
    banned: bool | None = None


class AdminUserPatchOut(BaseModel):
    updated: bool
    userId: str


class AdminRegenerateApiKeyOut(BaseModel):
    apiKey: str = Field(description="Shown once; store securely.")
    apiKeyPrefix: str


class PlatformMispOut(BaseModel):
    mispFallbackUrl: str | None = None
    hasMispFallbackApiKey: bool = False


class PlatformMispPut(BaseModel):
    """Omit a field to leave it unchanged. Empty string clears URL or API key ciphertext."""

    misp_fallback_url: str | None = Field(default=None)
    misp_fallback_api_key: str | None = Field(
        default=None,
        max_length=512,
        description="Omit to keep existing key; empty string clears; non-empty sets new key.",
    )


class PlatformMispPutOut(BaseModel):
    saved: bool
    mispFallbackUrl: str | None = None
    hasMispFallbackApiKey: bool = False
