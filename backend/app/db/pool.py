"""asyncpg connection pool lifecycle."""

from __future__ import annotations

import asyncpg

from app.db.conn_params import ssl_connect_arg


async def create_pool(dsn: str, *, database_ssl: str | None = None) -> asyncpg.Pool:
    kw: dict = {"min_size": 1, "max_size": 10, "command_timeout": 60}
    ssl = ssl_connect_arg(database_ssl)
    if ssl:
        kw["ssl"] = ssl
    return await asyncpg.create_pool(dsn, **kw)


async def close_pool(pool: asyncpg.Pool | None) -> None:
    if pool is not None:
        await pool.close()
