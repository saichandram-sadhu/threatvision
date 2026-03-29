"""Recent IOC activity for dashboard (spec §4.7)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class FlaggedByChip(BaseModel):
    """Source that flagged the IOC as malicious or suspicious."""

    id: str
    display_name: str


class ActivityRecentItem(BaseModel):
    id: str
    ioc_snippet: str
    verdict: str
    created_at: datetime
    flagged_by: list[FlaggedByChip] = Field(default_factory=list)


class ActivityRecentResponse(BaseModel):
    items: list[ActivityRecentItem] = Field(default_factory=list)
