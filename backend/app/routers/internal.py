"""Internal routes (BFF-only)."""

from __future__ import annotations

import hmac
import uuid
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.auth.internal_jwt import create_internal_token
from app.config import get_settings
from app.deps import get_pool

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
    request: Request,
    body: ExchangeIn,
    x_service_key: Annotated[str | None, Header(alias="X-Service-Key")] = None,
) -> ExchangeOut:
    settings = get_settings()
    expected = settings.bff_service_key
    if x_service_key is None:
        raise HTTPException(status_code=401, detail="Missing service key")
    if len(x_service_key) != len(expected) or not hmac.compare_digest(x_service_key, expected):
        raise HTTPException(status_code=401, detail="Invalid service key")

    try:
        uid = uuid.UUID(body.user_id.strip())
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid user id") from e

    pool = await get_pool(request)
    row = await pool.fetchrow(
        """
        SELECT id::text AS id, role::text AS role, banned
        FROM users
        WHERE id = $1
        """,
        uid,
    )
    if row is None:
        raise HTTPException(status_code=403, detail="User not found")
    if row["banned"]:
        raise HTTPException(status_code=403, detail="Account disabled")
    if row["role"] != body.role:
        raise HTTPException(
            status_code=403,
            detail="Role mismatch — session role does not match account. Sign in again.",
        )

    token = create_internal_token(row["id"], row["role"], settings=settings)
    return ExchangeOut(
        access_token=token,
        expires_in=settings.internal_jwt_expire_minutes * 60,
    )
