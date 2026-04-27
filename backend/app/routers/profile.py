"""Signed-in user profile + API key self-service (internal JWT, M16)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.auth.api_key import generate_api_key
from app.auth.internal_jwt import InternalUser, get_current_internal_user
from app.config import Settings, get_settings_dep
from app.deps import PoolDep
from app.schemas.profile import ProfileActivityItem, ProfileOut, RegenerateApiKeySelfOut

router = APIRouter(tags=["profile"])


def _mask_api_key(prefix: str | None) -> str:
    if not prefix or not str(prefix).strip():
        return "••••••••••••"
    p = str(prefix).strip()
    return f"{p}{'•' * 12}"


@router.get("/me/profile", response_model=ProfileOut)
async def read_my_profile(
    pool: PoolDep,
    user: Annotated[InternalUser, Depends(get_current_internal_user)],
) -> ProfileOut:
    uid = uuid.UUID(user.user_id)
    row = await pool.fetchrow(
        """
        SELECT email, role::text AS role, api_key_prefix, api_key_hash, daily_limit, unlimited, banned
        FROM users
        WHERE id = $1
        """,
        uid,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")

    has_key = row["api_key_hash"] is not None
    masked = _mask_api_key(row["api_key_prefix"]) if has_key else "(no key on file)"

    today = await pool.fetchval(
        """
        SELECT COALESCE(request_count, 0)
        FROM usage_counters
        WHERE user_id = $1 AND usage_day = (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')::date
        """,
        uid,
    )
    if today is None:
        today = 0

    week = await pool.fetchval(
        """
        SELECT COALESCE(SUM(request_count), 0)::bigint
        FROM usage_counters
        WHERE user_id = $1
          AND usage_day >= (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')::date - INTERVAL '6 days'
        """,
        uid,
    )
    if week is None:
        week = 0

    act_rows = await pool.fetch(
        """
        SELECT ioc_snippet, verdict, created_at
        FROM activity_log
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT 25
        """,
        uid,
    )

    return ProfileOut(
        user_id=user.user_id,
        email=row["email"],
        role=row["role"],
        api_key_masked=masked,
        has_api_key=has_key,
        daily_limit=row["daily_limit"],
        unlimited=row["unlimited"],
        banned=row["banned"],
        usage_today=int(today),
        usage_last_7d=int(week),
        recent_activity=[
            ProfileActivityItem(
                ioc_snippet=str(r["ioc_snippet"]),
                verdict=str(r["verdict"]),
                created_at=r["created_at"],
            )
            for r in act_rows
        ],
    )


@router.post("/me/regenerate-api-key", response_model=RegenerateApiKeySelfOut)
async def regenerate_my_api_key(
    pool: PoolDep,
    user: Annotated[InternalUser, Depends(get_current_internal_user)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> RegenerateApiKeySelfOut:
    uid = uuid.UUID(user.user_id)
    banned = await pool.fetchval("SELECT banned FROM users WHERE id = $1", uid)
    if banned is None:
        raise HTTPException(status_code=404, detail="User not found")
    if banned:
        raise HTTPException(status_code=403, detail="Account disabled")

    plain, digest, prefix = generate_api_key(settings.api_key_pepper)
    await pool.execute(
        """
        UPDATE users
        SET api_key_hash = $2, api_key_prefix = $3
        WHERE id = $1
        """,
        uid,
        digest,
        prefix,
    )
    return RegenerateApiKeySelfOut(apiKey=plain, apiKeyPrefix=prefix)
