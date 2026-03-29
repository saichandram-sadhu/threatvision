"""Per-source IOC result shapes (spec §4.2–4.3)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

SourceStatus = Literal["ok", "not_configured", "unavailable"]
SourceVerdict = Literal["clean", "suspicious", "malicious", "unknown"]
AggregateVerdict = Literal["CLEAN", "SUSPICIOUS", "MALICIOUS"]


class MispEventInfo(BaseModel):
    eventId: str
    eventName: str
    tags: list[str] = Field(default_factory=list)
    tlp: str = "unknown"
    feedName: str | None = None


class SourceResult(BaseModel):
    id: str
    displayName: str
    status: SourceStatus
    verdict: SourceVerdict | None = None
    detailLines: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    errorCode: str | None = None


class IocPayload(BaseModel):
    raw: str
    normalized: str
    type: str


class AggregateResult(BaseModel):
    verdict: AggregateVerdict
    confidence: int = Field(ge=0, le=100)
    rationale: str | None = None


class AnalyzeResponse(BaseModel):
    ioc: IocPayload
    aggregate: AggregateResult
    sources: list[SourceResult]
