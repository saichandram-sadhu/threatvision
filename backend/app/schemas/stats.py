"""Dashboard aggregate statistics (M13)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class VerdictBucket(BaseModel):
    verdict: str
    count: int = Field(ge=0)


class TopIpRow(BaseModel):
    ip: str
    count: int = Field(ge=0)


class DashboardStatsResponse(BaseModel):
    analyses_1d: int = Field(ge=0, description="Activity log rows in last 24h")
    analyses_7d: int = Field(ge=0)
    analyses_30d: int = Field(ge=0)
    analyses_all: int = Field(ge=0)
    verdict_distribution_30d: list[VerdictBucket] = Field(default_factory=list)
    top_ips_30d: list[TopIpRow] = Field(default_factory=list)
