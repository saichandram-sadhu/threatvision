"""Shared asyncpg options for hosted Postgres (Supabase, Neon, Railway Postgres with SSL, etc.)."""

from __future__ import annotations

import os

import asyncpg


def ssl_connect_arg(raw: str | None) -> str | None:
    """
    Map DATABASE_SSL env to asyncpg's ``ssl`` argument.

    Use ``DATABASE_SSL=require`` (or ``true`` / ``1``) for Supabase and other TLS-only hosts.
    Omit or ``disable`` for local Docker Postgres without TLS.
    """
    if raw is None or not str(raw).strip():
        return None
    v = str(raw).strip().lower()
    if v in ("0", "false", "no", "off", "disable"):
        return None
    return "require"


async def connect_pg(dsn: str, *, database_ssl: str | None = None) -> asyncpg.Connection:
    """
    Single asyncpg connection with optional TLS (Supabase, etc.).

    If ``database_ssl`` is omitted, reads ``DATABASE_SSL`` from the environment.
    """
    raw = database_ssl if database_ssl is not None else os.environ.get("DATABASE_SSL")
    ssl = ssl_connect_arg(raw)
    if ssl:
        return await asyncpg.connect(dsn, ssl=ssl)
    return await asyncpg.connect(dsn)
