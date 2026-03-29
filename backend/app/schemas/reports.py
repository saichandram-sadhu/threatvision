"""PDF report API (M8)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.source_result import AnalyzeResponse


class PdfReportIn(BaseModel):
    """Inline analysis payloads (persisted analysis IDs are not required for M8)."""

    analyses: list[AnalyzeResponse] = Field(..., min_length=1, max_length=50)
