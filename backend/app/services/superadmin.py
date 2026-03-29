"""Bootstrap SUPERADMIN from env email (spec — at most one superadmin)."""

from __future__ import annotations

import asyncpg

from app.config import Settings, get_settings


async def maybe_promote_superadmin(
    pool: asyncpg.Pool,
    *,
    user_id: str,
    email_normalized: str,
    settings: Settings | None = None,
) -> None:
    """If email matches ``SUPERADMIN_EMAIL`` and no other superadmin exists, promote user."""
    cfg = settings or get_settings()
    target = cfg.superadmin_email.strip().lower()
    if email_normalized != target:
        return

    async with pool.acquire() as conn:
        async with conn.transaction():
            me = await conn.fetchrow(
                """
                SELECT role::text AS role
                FROM users
                WHERE id = $1::uuid
                FOR UPDATE
                """,
                user_id,
            )
            if me is None:
                return
            if me["role"] == "SUPERADMIN":
                return

            others = await conn.fetchval(
                """
                SELECT COUNT(*)::int
                FROM users
                WHERE role = 'SUPERADMIN' AND id <> $1::uuid
                """,
                user_id,
            )
            if others and others > 0:
                return

            await conn.execute(
                """
                UPDATE users
                SET role = 'SUPERADMIN'
                WHERE id = $1::uuid
                """,
                user_id,
            )
