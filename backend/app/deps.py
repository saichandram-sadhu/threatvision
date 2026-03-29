"""Shared FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

import asyncpg
from fastapi import Depends, HTTPException, Request


async def get_pool(request: Request) -> asyncpg.Pool:
    pool: asyncpg.Pool | None = getattr(request.app.state, "pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    return pool


PoolDep = Annotated[asyncpg.Pool, Depends(get_pool)]
