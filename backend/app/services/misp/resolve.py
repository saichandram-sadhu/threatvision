"""Resolve MISP base URL + API key: user settings → platform fallback (spec §2)."""

from __future__ import annotations

import uuid

import asyncpg

from app.services.crypto import CryptoError, decrypt_secret


def normalize_misp_base_url(url: str) -> str:
    u = url.strip().rstrip("/")
    if not u.startswith(("http://", "https://")):
        u = f"https://{u}"
    return u


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
            return normalize_misp_base_url(row["misp_base_url"]), key, "user"
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
            return normalize_misp_base_url(plat["misp_fallback_url"]), key, "platform_fallback"
        except CryptoError:
            pass

    return None, None, "none"
