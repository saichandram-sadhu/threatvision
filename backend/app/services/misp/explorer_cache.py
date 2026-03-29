"""Short-TTL JSON cache for MISP Explorer (M4.4)."""

from __future__ import annotations

import json
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import asyncpg

from app.schemas.misp_explorer import MispExplorerResponse

CACHE_TTL_SECONDS = 30


async def get_explorer_cached_or_fetch(
    pool: asyncpg.Pool,
    user_id: str,
    fetch: Callable[[], Awaitable[MispExplorerResponse]],
) -> MispExplorerResponse:
    uid = uuid.UUID(user_id)
    now = datetime.now(tz=UTC)
    row = await pool.fetchrow(
        """
        SELECT payload, updated_at
        FROM misp_explorer_cache
        WHERE user_id = $1
        """,
        uid,
    )
    if row is not None:
        age = (now - row["updated_at"]).total_seconds()
        if age < CACHE_TTL_SECONDS:
            return MispExplorerResponse.model_validate(row["payload"])

    fresh = await fetch()
    dumped = json.dumps(fresh.model_dump(mode="json"), default=str)
    await pool.execute(
        """
        INSERT INTO misp_explorer_cache (user_id, payload, updated_at)
        VALUES ($1, $2::jsonb, NOW())
        ON CONFLICT (user_id) DO UPDATE SET
            payload = EXCLUDED.payload,
            updated_at = NOW()
        """,
        uid,
        dumped,
    )
    return fresh
