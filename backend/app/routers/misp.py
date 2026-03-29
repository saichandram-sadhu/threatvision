"""MISP settings probe and Instance Explorer (internal JWT)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.internal_jwt import InternalUser, get_current_internal_user
from app.deps import PoolDep
from app.schemas.misp_explorer import MispExplorerResponse
from app.services.crypto import encrypt_secret
from app.services.misp.explorer import build_explorer_snapshot
from app.services.misp.explorer_cache import get_explorer_cached_or_fetch
from app.services.misp.http import misp_ping_version
from app.services.misp.resolve import normalize_misp_base_url, resolve_misp_for_user

router = APIRouter(tags=["misp"])


class MispTestBody(BaseModel):
    """Omit both fields to use stored user MISP or platform fallback."""

    base_url: str | None = None
    api_key: str | None = Field(default=None, description="Plaintext API key (not stored by this endpoint)")


class MispTestOut(BaseModel):
    ok: bool
    version: str | None = None
    resolution: str
    detail: str | None = None


class MispSaveBody(BaseModel):
    base_url: str = Field(min_length=4, max_length=2048)
    api_key: str = Field(min_length=8, max_length=512)


class MispSaveOut(BaseModel):
    saved: bool
    base_url: str


@router.post("/settings/misp/test", response_model=MispTestOut)
async def test_misp_connection(
    body: MispTestBody,
    pool: PoolDep,
    user: Annotated[InternalUser, Depends(get_current_internal_user)],
) -> MispTestOut:
    url = (body.base_url or "").strip() or None
    key = body.api_key
    resolution = "inline_test"

    if not url or not key:
        u, k, tag = await resolve_misp_for_user(pool, user.user_id)
        url, key, resolution = u, k, tag
        if resolution == "none":
            return MispTestOut(
                ok=False,
                resolution="none",
                detail="MISP is not configured (user settings or platform fallback).",
            )

    assert url and key
    try:
        data = await misp_ping_version(url, key)
        ver = data.get("version") or data.get("Version")
        return MispTestOut(ok=True, version=str(ver) if ver is not None else None, resolution=resolution)
    except Exception as e:  # noqa: BLE001
        return MispTestOut(
            ok=False,
            resolution=resolution,
            detail=str(e),
        )


@router.put("/settings/misp", response_model=MispSaveOut)
async def save_misp_settings(
    body: MispSaveBody,
    pool: PoolDep,
    user: Annotated[InternalUser, Depends(get_current_internal_user)],
) -> MispSaveOut:
    normalized = normalize_misp_base_url(body.base_url)
    ciphertext = encrypt_secret(body.api_key)
    await pool.execute(
        """
        INSERT INTO user_integration_settings (
            user_id, source_toggles, misp_base_url, misp_api_key_ciphertext, updated_at
        )
        VALUES ($1::uuid, '{}'::jsonb, $2, $3, NOW())
        ON CONFLICT (user_id) DO UPDATE SET
            misp_base_url = EXCLUDED.misp_base_url,
            misp_api_key_ciphertext = EXCLUDED.misp_api_key_ciphertext,
            updated_at = NOW()
        """,
        user.user_id,
        normalized,
        ciphertext,
    )
    return MispSaveOut(saved=True, base_url=normalized)


@router.get("/misp/explorer", response_model=MispExplorerResponse)
async def misp_explorer(
    pool: PoolDep,
    user: Annotated[InternalUser, Depends(get_current_internal_user)],
) -> MispExplorerResponse:
    url, key, resolution = await resolve_misp_for_user(pool, user.user_id)
    if not url or not key:
        raise HTTPException(
            status_code=400,
            detail="MISP is not configured. Save URL and API key under settings or set platform fallback.",
        )

    async def fetch() -> MispExplorerResponse:
        return await build_explorer_snapshot(url, key, resolution=resolution)

    return await get_explorer_cached_or_fetch(pool, user.user_id, fetch)
