"""Shared FastAPI dependencies."""

from __future__ import annotations

import logging
from typing import Annotated

import asyncpg
from fastapi import Depends, HTTPException, Request

from app.config import get_settings
from app.db.pool import create_pool

_log = logging.getLogger(__name__)


async def get_pool(request: Request) -> asyncpg.Pool:
    pool: asyncpg.Pool | None = getattr(request.app.state, "pool", None)
    if pool is not None:
        return pool

    settings = get_settings()
    if not settings.database_url:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable — DATABASE_URL is not configured.",
        )
    try:
        pool = await create_pool(settings.database_url, database_ssl=settings.database_ssl)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail="Database unavailable — start PostgreSQL (e.g. docker compose up -d in threatvision/).",
        ) from e
    request.app.state.pool = pool
    _log.info("PostgreSQL pool created after startup (lazy connect).")
    return pool


PoolDep = Annotated[asyncpg.Pool, Depends(get_pool)]
