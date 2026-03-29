"""Internal routes (BFF-only)."""

from __future__ import annotations

import hmac
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.auth.internal_jwt import create_internal_token
from app.config import get_settings

router = APIRouter()


class ExchangeIn(BaseModel):
    user_id: str = Field(min_length=1)
    role: str = Field(pattern="^(USER|ADMIN|SUPERADMIN)$")


class ExchangeOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/internal/auth/exchange", response_model=ExchangeOut)
async def auth_exchange(
    body: ExchangeIn,
    x_service_key: Annotated[str | None, Header(alias="X-Service-Key")] = None,
) -> ExchangeOut:
    settings = get_settings()
    expected = settings.bff_service_key
    if x_service_key is None:
        raise HTTPException(status_code=401, detail="Missing service key")
    if len(x_service_key) != len(expected) or not hmac.compare_digest(x_service_key, expected):
        raise HTTPException(status_code=401, detail="Invalid service key")

    token = create_internal_token(body.user_id, body.role, settings=settings)
    return ExchangeOut(
        access_token=token,
        expires_in=settings.internal_jwt_expire_minutes * 60,
    )
