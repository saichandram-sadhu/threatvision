"""Versioned public API (API key auth)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.api_key import ApiKeyUser, get_current_user_api_key

router = APIRouter()


class MeOut(BaseModel):
    user_id: str
    email: str
    role: str


@router.get("/v1/me", response_model=MeOut)
async def read_me(user: Annotated[ApiKeyUser, Depends(get_current_user_api_key)]) -> MeOut:
    return MeOut(user_id=user.user_id, email=user.email, role=user.role)
