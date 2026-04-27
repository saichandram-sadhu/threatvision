"""Current-user profile (M16)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class ProfileActivityItem(BaseModel):
    ioc_snippet: str
    verdict: str
    created_at: datetime


class ProfileOut(BaseModel):
    user_id: str
    email: EmailStr
    role: str
    """Masked API key hint (prefix + bullets); never the full secret."""
    api_key_masked: str
    has_api_key: bool
    daily_limit: int
    unlimited: bool
    banned: bool
    usage_today: int = Field(ge=0)
    usage_last_7d: int = Field(ge=0)
    recent_activity: list[ProfileActivityItem] = Field(default_factory=list)


class RegenerateApiKeySelfOut(BaseModel):
    apiKey: str = Field(description="Shown once; store securely.")
    apiKeyPrefix: str
