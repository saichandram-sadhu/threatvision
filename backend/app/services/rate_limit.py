"""Per-user daily request limits (Postgres only — spec §2)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import asyncpg
from fastapi import HTTPException


async def check_and_increment_daily(pool: asyncpg.Pool, user_id: UUID) -> None:
    """
    Increment today's counter for ``user_id`` or raise 429 if at/over limit.
    Call inside authenticated IOC/analyze/bulk handlers (M6+).
    """
    today = datetime.now(tz=UTC).date()

    async with pool.acquire() as conn:
        async with conn.transaction():
            u = await conn.fetchrow(
                """
                SELECT daily_limit, unlimited, banned
                FROM users
                WHERE id = $1
                FOR UPDATE
                """,
                user_id,
            )
            if u is None:
                raise HTTPException(status_code=401, detail="User not found")
            if u["banned"]:
                raise HTTPException(status_code=403, detail="Account disabled")
            if u["unlimited"]:
                return

            limit: int = u["daily_limit"]
            row = await conn.fetchrow(
                """
                SELECT request_count
                FROM usage_counters
                WHERE user_id = $1 AND usage_day = $2
                FOR UPDATE
                """,
                user_id,
                today,
            )
            current = int(row["request_count"]) if row else 0
            if current >= limit:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "rate_limit_exceeded",
                        "limit": limit,
                        "used": current,
                    },
                )

            if row is None:
                await conn.execute(
                    """
                    INSERT INTO usage_counters (user_id, usage_day, request_count)
                    VALUES ($1, $2, 1)
                    """,
                    user_id,
                    today,
                )
            else:
                await conn.execute(
                    """
                    UPDATE usage_counters
                    SET request_count = request_count + 1
                    WHERE user_id = $1 AND usage_day = $2
                    """,
                    user_id,
                    today,
                )
