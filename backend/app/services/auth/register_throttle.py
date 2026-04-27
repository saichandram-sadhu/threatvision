"""Registration rate limits: client IP + normalized email, UTC hour buckets."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import asyncpg
from fastapi import HTTPException, Request


def client_ip_from_request(request: Request) -> str:
    """Best-effort client IP; honor X-Forwarded-For first hop (place app behind a trusted proxy)."""
    forwarded = (request.headers.get("x-forwarded-for") or "").strip()
    if forwarded:
        part = forwarded.split(",")[0].strip()
        if part and len(part) <= 80:
            return part
    if request.client and request.client.host:
        return request.client.host[:80]
    return "unknown"


def _utc_hour_start() -> datetime:
    now = datetime.now(tz=UTC)
    return now.replace(minute=0, second=0, microsecond=0)


async def enforce_registration_throttle(
    pool: asyncpg.Pool,
    *,
    client_ip: str,
    email_normalized: str,
    ip_max_per_hour: int,
    email_max_per_hour: int,
) -> None:
    if ip_max_per_hour < 1 or email_max_per_hour < 1:
        return
    window = _utc_hour_start()
    prune_before = window - timedelta(hours=48)
    ip_key = f"ip:{client_ip[:80]}"
    em_key = f"email:{email_normalized[:320]}"

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "DELETE FROM registration_throttle WHERE window_start < $1",
                prune_before,
            )
            for bucket, limit in (
                (ip_key, ip_max_per_hour),
                (em_key, email_max_per_hour),
            ):
                row = await conn.fetchrow(
                    """
                    INSERT INTO registration_throttle (bucket, window_start, hit_count)
                    VALUES ($1, $2, 1)
                    ON CONFLICT (bucket, window_start)
                    DO UPDATE SET hit_count = registration_throttle.hit_count + 1
                    RETURNING hit_count
                    """,
                    bucket,
                    window,
                )
                cnt = int(row["hit_count"]) if row else 0
                if cnt > limit:
                    raise HTTPException(
                        status_code=429,
                        detail={
                            "error": "registration_rate_limited",
                            "message": "Too many registration attempts. Try again later.",
                        },
                    )
