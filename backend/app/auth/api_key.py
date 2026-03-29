"""Programmatic API key verification (HMAC-SHA256 with server pepper)."""

from __future__ import annotations

import hashlib
import hmac
import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException

from app.config import Settings, get_settings_dep
from app.deps import PoolDep


@dataclass(frozen=True)
class ApiKeyUser:
    user_id: str
    email: str
    role: str


def compute_api_key_hash(raw_key: str, pepper: str) -> str:
    return hmac.new(
        pepper.encode("utf-8"),
        raw_key.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def generate_api_key(pepper: str) -> tuple[str, str, str]:
    """Return (plaintext_key, hash_for_db, display_prefix)."""
    plain = str(uuid.uuid4())
    digest = compute_api_key_hash(plain, pepper)
    prefix = plain.replace("-", "")[:8]
    return plain, digest, prefix


def _extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None


async def get_current_user_api_key(
    pool: PoolDep,
    settings: Annotated[Settings, Depends(get_settings_dep)],
    authorization: Annotated[str | None, Header()] = None,
) -> ApiKeyUser:
    raw = _extract_bearer(authorization)
    if raw is None:
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    digest = compute_api_key_hash(raw, settings.api_key_pepper)
    row = await pool.fetchrow(
        """
        SELECT id::text AS id, email, role::text AS role, banned
        FROM users
        WHERE api_key_hash = $1
        """,
        digest,
    )
    if row is None or row["banned"]:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return ApiKeyUser(user_id=row["id"], email=row["email"], role=row["role"])
