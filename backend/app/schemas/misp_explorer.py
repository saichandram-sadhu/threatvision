"""MISP Instance Explorer DTO (spec §4.10)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MispFeedRow(BaseModel):
    id: str | None = None
    name: str | None = None
    url: str | None = None
    source_format: str | None = Field(default=None, description="MISP / CSV / freetext / unknown")
    enabled: bool | None = None
    last_fetch: datetime | None = None
    event_count: int | None = Field(default=None, description="Best-effort; may be unknown")
    live_sync: bool | None = Field(default=None, description="Enabled feed / scheduling hint")
    cache_age_seconds: int | None = Field(default=None, description="Seconds since last_fetch if known")


class MispServerRow(BaseModel):
    id: str | None = None
    name: str | None = None
    url: str | None = None
    push: bool | None = None
    pull: bool | None = None
    last_sync: datetime | None = None
    sync_status: str | None = Field(default=None, description="success | failed | never | unknown")
    event_count: int | None = None


class MispTaxonomyRow(BaseModel):
    namespace: str | None = None
    enabled: bool | None = None
    description: str | None = None


class MispStatsPanel(BaseModel):
    total_events: int | None = None
    total_attributes: int | None = None
    total_objects: int | None = None
    feeds_configured: int | None = None
    feeds_enabled: int | None = None
    connected_servers: int | None = None
    misp_version: str | None = None
    last_event_added: datetime | None = None


class MispExplorerResponse(BaseModel):
    connected: bool = True
    base_url: str
    resolution: str = Field(
        default="user",
        description="user | platform_fallback | inline_test",
    )
    misp_version: str | None = None
    feeds: list[MispFeedRow] = Field(default_factory=list)
    servers: list[MispServerRow] = Field(default_factory=list)
    taxonomies: list[MispTaxonomyRow] = Field(default_factory=list)
    stats: MispStatsPanel = Field(default_factory=MispStatsPanel)
    sync_indicator: str = Field(default="idle", description="syncing | idle | error")
    source_errors: dict[str, str] = Field(default_factory=dict)
    fetched_at: datetime
    raw_version: dict[str, Any] | None = Field(default=None, exclude=True)
