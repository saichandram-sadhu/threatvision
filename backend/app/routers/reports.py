"""PDF reports (M8)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.auth.internal_jwt import InternalUser, get_current_internal_user
from app.config import Settings, get_settings_dep
from app.deps import PoolDep
from app.schemas.reports import PdfReportIn
from app.services.rate_limit import check_and_increment_daily
from app.services.reports.gemini import summarize_analyses
from app.services.reports.pdf import build_pdf_bytes

router = APIRouter(tags=["reports"])


@router.post("/reports/pdf")
async def generate_pdf_report(
    body: PdfReportIn,
    pool: PoolDep,
    user: Annotated[InternalUser, Depends(get_current_internal_user)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> Response:
    await check_and_increment_daily(pool, UUID(user.user_id))
    summary = await summarize_analyses(settings.gemini_api_key, body.analyses)
    try:
        pdf = await build_pdf_bytes(body.analyses, summary)
    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail={"error": "pdf_engine_unavailable", "message": str(e)},
        ) from e
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="threatvision-report.pdf"',
        },
    )
