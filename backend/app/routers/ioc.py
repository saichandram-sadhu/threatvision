"""IOC analysis (internal JWT + rate limits)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.internal_jwt import InternalUser, get_current_internal_user
from app.deps import PoolDep
from app.schemas.source_result import AnalyzeResponse
from app.services.ioc.analyze import analyze_ioc_value
from app.services.ioc.input_errors import IocInputError
from app.services.rate_limit import check_and_increment_daily

router = APIRouter(tags=["ioc"])


class AnalyzeIn(BaseModel):
    ioc: str = Field(min_length=1, max_length=16384)


@router.post("/ioc/analyze", response_model=AnalyzeResponse)
async def analyze_ioc(
    body: AnalyzeIn,
    pool: PoolDep,
    user: Annotated[InternalUser, Depends(get_current_internal_user)],
) -> AnalyzeResponse:
    await check_and_increment_daily(pool, UUID(user.user_id))
    try:
        return await analyze_ioc_value(pool, user_id=user.user_id, raw_ioc=body.ioc)
    except IocInputError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
