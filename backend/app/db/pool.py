"""asyncpg connection pool lifecycle."""

from __future__ import annotations

import asyncpg


async def create_pool(dsn: str) -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn, min_size=1, max_size=10, command_timeout=60)


async def close_pool(pool: asyncpg.Pool | None) -> None:
    if pool is not None:
        await pool.close()
