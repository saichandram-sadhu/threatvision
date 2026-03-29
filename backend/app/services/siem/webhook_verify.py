"""Authenticate SIEM webhook requests (bearer hash + optional HMAC timestamp)."""

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass
import asyncpg
from fastapi import HTTPException

from app.auth.api_key import compute_api_key_hash
from app.config import Settings


@dataclass(frozen=True)
class WebhookEndpointRow:
    user_id: str
    secret_hash: str | None
    hmac_optional: bool


_MAX_SKEW_SEC = 300


async def fetch_webhook_by_path_key(pool: asyncpg.Pool, path_key: str) -> WebhookEndpointRow | None:
    if not path_key or len(path_key) > 80:
        return None
    row = await pool.fetchrow(
        """
        SELECT ws.user_id::text AS user_id, ws.secret_hash, ws.hmac_optional, u.banned
        FROM webhook_secrets ws
        JOIN users u ON u.id = ws.user_id
        WHERE ws.path_key = $1
        """,
        path_key,
    )
    if row is None:
        return None
    if row["banned"]:
        raise HTTPException(status_code=403, detail="Account disabled")
    sh = row["secret_hash"]
    if isinstance(sh, str) and not sh.strip():
        sh = None
    return WebhookEndpointRow(
        user_id=row["user_id"],
        secret_hash=sh,
        hmac_optional=bool(row["hmac_optional"]),
    )


def _verify_bearer_secret(plain: str | None, stored_hash: str | None, pepper: str) -> bool:
    if stored_hash is None:
        return True
    if not plain:
        return False
    digest = compute_api_key_hash(plain, pepper)
    return hmac.compare_digest(digest, stored_hash)


def verify_hmac_body(
    secret_plain: str,
    timestamp_unix: int,
    body: bytes,
    signature_hex: str,
) -> bool:
    msg = f"{timestamp_unix}.".encode("utf-8") + body
    expected = hmac.new(secret_plain.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    try:
        return hmac.compare_digest(expected.lower(), signature_hex.strip().lower())
    except Exception:  # noqa: BLE001
        return False


def assert_timestamp_fresh(ts: int, *, max_skew: int = _MAX_SKEW_SEC) -> None:
    now = int(time.time())
    if abs(now - ts) > max_skew:
        raise HTTPException(
            status_code=401,
            detail={"error": "timestamp_skew", "max_skew_seconds": max_skew},
        )


def authenticate_webhook(
    row: WebhookEndpointRow,
    settings: Settings,
    *,
    webhook_secret_header: str | None,
    timestamp_header: str | None,
    signature_hex: str | None,
    body: bytes,
) -> None:
    """
    Validate bearer (HMAC-SHA256 with API_KEY_PEPPER, same as API keys) and optional request HMAC.
    When ``hmac_optional`` is true, ``X-Tv-Webhook-Secret`` must be supplied and must match
    ``secret_hash``; the same plaintext is used as the HMAC key for the body.
    """
    if row.hmac_optional and row.secret_hash is None:
        raise HTTPException(
            status_code=503,
            detail="Webhook HMAC is enabled but no bearer secret_hash is configured",
        )

    if row.secret_hash is not None and not _verify_bearer_secret(
        webhook_secret_header,
        row.secret_hash,
        settings.api_key_pepper,
    ):
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    if row.hmac_optional:
        if not webhook_secret_header:
            raise HTTPException(status_code=401, detail="X-Tv-Webhook-Secret required for HMAC webhooks")
        if timestamp_header is None or signature_hex is None:
            raise HTTPException(
                status_code=401,
                detail="X-Tv-Timestamp and X-Tv-Signature required for HMAC webhooks",
            )
        try:
            ts = int(timestamp_header)
        except ValueError as e:
            raise HTTPException(status_code=401, detail="Invalid X-Tv-Timestamp") from e
        assert_timestamp_fresh(ts)
        if not verify_hmac_body(webhook_secret_header, ts, body, signature_hex):
            raise HTTPException(status_code=401, detail="Invalid HMAC signature")
