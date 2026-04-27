"""Resolve MISP base URL + API key: user settings → platform fallback (spec §2)."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import asyncpg

from app.services.crypto import CryptoError, decrypt_secret


def normalize_misp_base_url(url: str) -> str:
    u = url.strip().rstrip("/")
    if not u.startswith(("http://", "https://")):
        u = f"https://{u}"
    return u


# (mtime_ns, url, key) — re-read backend/.env when it changes (get_settings() is lru_cached).
_dotenv_misp_cache: tuple[int | None, str | None, str | None] = (None, None, None)


def _backend_dotenv_path() -> Path:
    return Path(__file__).resolve().parents[3] / ".env"


def _platform_from_os_environ() -> tuple[str | None, str | None]:
    u = (os.environ.get("PLATFORM_MISP_URL") or "").strip()
    k = (os.environ.get("PLATFORM_MISP_API_KEY") or "").strip()
    if u and k:
        return normalize_misp_base_url(u), k
    return None, None


def _platform_from_dotenv_file() -> tuple[str | None, str | None]:
    """Fresh read of PLATFORM_MISP_* from backend/.env (avoids stale get_settings cache)."""
    global _dotenv_misp_cache
    if os.environ.get("THREATVISION_SKIP_LOCAL_ENV_MISP", "").strip().lower() in (
        "1",
        "true",
        "yes",
    ):
        return None, None
    path = _backend_dotenv_path()
    if not path.is_file():
        return None, None
    try:
        mtime = path.stat().st_mtime_ns
    except OSError:
        return None, None
    if _dotenv_misp_cache[0] == mtime:
        u, k = _dotenv_misp_cache[1], _dotenv_misp_cache[2]
        if u and k:
            return u, k
        return None, None

    url_v: str | None = None
    key_v: str | None = None
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        k, v = k.strip(), v.strip()
        if not v:
            continue
        if k == "PLATFORM_MISP_URL":
            url_v = v
        elif k == "PLATFORM_MISP_API_KEY":
            key_v = v

    if url_v and key_v:
        nu, nk = normalize_misp_base_url(url_v), key_v
        _dotenv_misp_cache = (mtime, nu, nk)
        return nu, nk
    _dotenv_misp_cache = (mtime, None, None)
    return None, None


async def resolve_misp_for_user(
    pool: asyncpg.Pool,
    user_id: str,
) -> tuple[str | None, str | None, str]:
    """
    Return ``(base_url, api_key_plain, resolution_tag)``.
    ``resolution_tag`` is ``user``, ``platform_fallback``, or ``none``.
    """
    uid = uuid.UUID(user_id)
    row = await pool.fetchrow(
        """
        SELECT misp_base_url, misp_api_key_ciphertext
        FROM user_integration_settings
        WHERE user_id = $1
        """,
        uid,
    )
    if row and row["misp_base_url"] and row["misp_api_key_ciphertext"]:
        try:
            key = decrypt_secret(row["misp_api_key_ciphertext"])
            url = normalize_misp_base_url(row["misp_base_url"].strip())
            if url and key.strip():
                return url, key.strip(), "user"
        except CryptoError:
            pass

    plat = await pool.fetchrow(
        """
        SELECT misp_fallback_url, misp_fallback_api_key_ciphertext
        FROM platform_settings
        WHERE id = 1
        """,
    )
    if plat and plat["misp_fallback_url"] and plat["misp_fallback_api_key_ciphertext"]:
        try:
            key = decrypt_secret(plat["misp_fallback_api_key_ciphertext"])
            url = normalize_misp_base_url(plat["misp_fallback_url"])
            if url and key.strip():
                return url, key.strip(), "platform_fallback"
        except CryptoError:
            pass

    eu, ek = _platform_from_os_environ()
    if eu and ek:
        return eu, ek, "platform_env"

    fu, fk = _platform_from_dotenv_file()
    if fu and fk:
        return fu, fk, "platform_env"

    return None, None, "none"
