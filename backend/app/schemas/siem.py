"""SIEM webhook response models (M9)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SiemIocResult(BaseModel):
    ioc: str
    normalized: str | None = None
    type: str | None = None
    verdict: str | None = None
    confidence: int | None = None
    error: str | None = None


class SiemWebhookResult(BaseModel):
    accepted: bool = True
    iocCount: int
    analyzed: int = Field(description="Count of IOCs analyzed without error")
    results: list[SiemIocResult]
    message: str | None = None
