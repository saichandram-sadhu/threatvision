"""Bulk IOC job API shapes (M7)."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class BulkCreateIn(BaseModel):
    iocs: list[str] = Field(..., min_length=1, max_length=500)

    @field_validator("iocs")
    @classmethod
    def nonempty_and_bounded(cls, v: list[str]) -> list[str]:
        out = [s.strip() for s in v if s and s.strip()]
        if not out:
            raise ValueError("At least one non-empty IOC is required")
        if len(out) > 500:
            raise ValueError("Maximum 500 IOCs per job")
        for s in out:
            if len(s) > 16384:
                raise ValueError("Each IOC must be at most 16384 characters")
        return out


class BulkJobCreated(BaseModel):
    jobId: str
    itemCount: int
    status: str = "pending"
