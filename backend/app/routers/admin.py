"""Superadmin controls (M10) — internal JWT + env email alignment."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.auth.admin_deps import require_superadmin
from app.auth.api_key import generate_api_key
from app.auth.internal_jwt import InternalUser
from app.config import Settings, get_settings_dep
from app.deps import PoolDep
from app.schemas.admin import (
    AdminRegenerateApiKeyOut,
    AdminUserOut,
    AdminUserPatch,
    AdminUserPatchOut,
    PlatformMispOut,
    PlatformMispPut,
    PlatformMispPutOut,
)
from app.services.crypto import encrypt_secret
from app.services.misp.resolve import normalize_misp_base_url

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[AdminUserOut])
async def list_users(
    pool: PoolDep,
    _: Annotated[InternalUser, Depends(require_superadmin)],
) -> list[AdminUserOut]:
    rows = await pool.fetch(
        """
        SELECT id::text AS id, email, role::text AS role, daily_limit, unlimited, banned,
               api_key_prefix, created_at
        FROM users
        ORDER BY created_at DESC
        LIMIT 500
        """
    )
    return [
        AdminUserOut(
            userId=r["id"],
            email=r["email"],
            role=r["role"],
            dailyLimit=r["daily_limit"],
            unlimited=r["unlimited"],
            banned=r["banned"],
            apiKeyPrefix=r["api_key_prefix"],
            createdAt=r["created_at"],
        )
        for r in rows
    ]


@router.patch("/users/{user_id}", response_model=AdminUserPatchOut)
async def patch_user(
    user_id: str,
    body: AdminUserPatch,
    pool: PoolDep,
    admin: Annotated[InternalUser, Depends(require_superadmin)],
) -> AdminUserPatchOut:
    patch = body.model_dump(exclude_unset=True)
    if not patch:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        target = uuid.UUID(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid user id") from e

    admin_uid = uuid.UUID(admin.user_id)
    if patch.get("banned") is True and target == admin_uid:
        raise HTTPException(status_code=400, detail="Cannot ban your own account")

    exists = await pool.fetchval("SELECT 1 FROM users WHERE id = $1", target)
    if not exists:
        raise HTTPException(status_code=404, detail="User not found")

    sets: list[str] = []
    args: list[object] = []
    n = 1
    if "dailyLimit" in patch:
        sets.append(f"daily_limit = ${n}")
        args.append(patch["dailyLimit"])
        n += 1
    if "unlimited" in patch:
        sets.append(f"unlimited = ${n}")
        args.append(patch["unlimited"])
        n += 1
    if "banned" in patch:
        sets.append(f"banned = ${n}")
        args.append(patch["banned"])
        n += 1

    args.append(target)
    await pool.execute(
        f"UPDATE users SET {', '.join(sets)} WHERE id = ${n}",
        *args,
    )
    return AdminUserPatchOut(updated=True, userId=user_id)


@router.post("/users/{user_id}/regenerate-api-key", response_model=AdminRegenerateApiKeyOut)
async def regenerate_user_api_key(
    user_id: str,
    pool: PoolDep,
    settings: Annotated[Settings, Depends(get_settings_dep)],
    _: Annotated[InternalUser, Depends(require_superadmin)],
) -> AdminRegenerateApiKeyOut:
    try:
        target = uuid.UUID(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid user id") from e

    exists = await pool.fetchval("SELECT 1 FROM users WHERE id = $1", target)
    if not exists:
        raise HTTPException(status_code=404, detail="User not found")

    plain, digest, prefix = generate_api_key(settings.api_key_pepper)
    await pool.execute(
        """
        UPDATE users
        SET api_key_hash = $2, api_key_prefix = $3
        WHERE id = $1
        """,
        target,
        digest,
        prefix,
    )
    return AdminRegenerateApiKeyOut(apiKey=plain, apiKeyPrefix=prefix)


@router.get("/platform/misp", response_model=PlatformMispOut)
async def get_platform_misp(
    pool: PoolDep,
    _: Annotated[InternalUser, Depends(require_superadmin)],
) -> PlatformMispOut:
    row = await pool.fetchrow(
        """
        SELECT misp_fallback_url, misp_fallback_api_key_ciphertext
        FROM platform_settings
        WHERE id = 1
        """
    )
    if row is None:
        return PlatformMispOut()
    return PlatformMispOut(
        mispFallbackUrl=row["misp_fallback_url"],
        hasMispFallbackApiKey=bool(row["misp_fallback_api_key_ciphertext"]),
    )


@router.put("/platform/misp", response_model=PlatformMispPutOut)
async def put_platform_misp(
    body: PlatformMispPut,
    pool: PoolDep,
    _: Annotated[InternalUser, Depends(require_superadmin)],
) -> PlatformMispPutOut:
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="Provide at least one field to update")

    row = await pool.fetchrow(
        """
        SELECT misp_fallback_url, misp_fallback_api_key_ciphertext
        FROM platform_settings
        WHERE id = 1
        """
    )
    if row is None:
        raise HTTPException(status_code=503, detail="Platform settings row missing")

    url = row["misp_fallback_url"]
    ct = row["misp_fallback_api_key_ciphertext"]

    if "misp_fallback_url" in data:
        raw = data["misp_fallback_url"]
        if raw is None or (isinstance(raw, str) and raw.strip() == ""):
            url = None
        else:
            url = normalize_misp_base_url(str(raw))

    if "misp_fallback_api_key" in data:
        ak = data["misp_fallback_api_key"]
        if ak is None or (isinstance(ak, str) and ak.strip() == ""):
            ct = None
        else:
            ct = encrypt_secret(str(ak))

    await pool.execute(
        """
        UPDATE platform_settings
        SET misp_fallback_url = $1, misp_fallback_api_key_ciphertext = $2, updated_at = NOW()
        WHERE id = 1
        """,
        url,
        ct,
    )
    return PlatformMispPutOut(
        saved=True,
        mispFallbackUrl=url,
        hasMispFallbackApiKey=bool(ct),
    )
