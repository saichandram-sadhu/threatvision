"""Persistence helpers for bulk IOC jobs."""

from __future__ import annotations

import json
import uuid
from typing import Any

import asyncpg


async def insert_bulk_job(pool: asyncpg.Pool, user_id: uuid.UUID, iocs: list[str]) -> uuid.UUID:
    async with pool.acquire() as conn:
        async with conn.transaction():
            job_id = await conn.fetchval(
                """
                INSERT INTO ioc_jobs (user_id, status)
                VALUES ($1, 'pending')
                RETURNING id
                """,
                user_id,
            )
            for pos, raw in enumerate(iocs):
                await conn.execute(
                    """
                    INSERT INTO ioc_job_items (job_id, ioc_raw, position, item_status)
                    VALUES ($1, $2, $3, 'pending')
                    """,
                    job_id,
                    raw,
                    pos,
                )
            return job_id


async def get_job_for_user(
    pool: asyncpg.Pool,
    job_id: uuid.UUID,
    user_id: uuid.UUID,
) -> asyncpg.Record | None:
    return await pool.fetchrow(
        """
        SELECT id, user_id, status, created_at, updated_at
        FROM ioc_jobs
        WHERE id = $1 AND user_id = $2
        """,
        job_id,
        user_id,
    )


async def claim_job_processing(pool: asyncpg.Pool, job_id: uuid.UUID) -> bool:
    row = await pool.fetchrow(
        """
        UPDATE ioc_jobs
        SET status = 'processing', updated_at = NOW()
        WHERE id = $1 AND status = 'pending'
        RETURNING id
        """,
        job_id,
    )
    return row is not None


async def fetch_job_items_ordered(pool: asyncpg.Pool, job_id: uuid.UUID) -> list[asyncpg.Record]:
    rows = await pool.fetch(
        """
        SELECT id, position, ioc_raw, ioc_type, item_status, aggregate, sources, error_message
        FROM ioc_job_items
        WHERE job_id = $1
        ORDER BY position ASC
        """,
        job_id,
    )
    return list(rows)


async def update_item_done(
    pool: asyncpg.Pool,
    item_id: uuid.UUID,
    ioc_type: str,
    aggregate: dict[str, Any],
    sources: list[dict[str, Any]],
) -> None:
    await pool.execute(
        """
        UPDATE ioc_job_items
        SET ioc_type = $2,
            aggregate = $3::jsonb,
            sources = $4::jsonb,
            item_status = 'done',
            error_message = NULL
        WHERE id = $1
        """,
        item_id,
        ioc_type,
        json.dumps(aggregate),
        json.dumps(sources),
    )


async def update_item_error(pool: asyncpg.Pool, item_id: uuid.UUID, message: str) -> None:
    await pool.execute(
        """
        UPDATE ioc_job_items
        SET item_status = 'error',
            error_message = $2
        WHERE id = $1
        """,
        item_id,
        message[:2000],
    )


async def mark_pending_items_rate_limited(pool: asyncpg.Pool, job_id: uuid.UUID) -> None:
    await pool.execute(
        """
        UPDATE ioc_job_items
        SET item_status = 'error', error_message = 'rate_limit_exceeded'
        WHERE job_id = $1 AND item_status = 'pending'
        """,
        job_id,
    )


async def set_job_status(
    pool: asyncpg.Pool,
    job_id: uuid.UUID,
    status: str,
) -> None:
    await pool.execute(
        """
        UPDATE ioc_jobs
        SET status = $2, updated_at = NOW()
        WHERE id = $1
        """,
        job_id,
        status,
    )
