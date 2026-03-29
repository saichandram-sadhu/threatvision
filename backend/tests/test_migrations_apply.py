"""Apply 001_initial.sql — integration test is opt-in (destructive to public schema)."""

from __future__ import annotations

import os

import pytest

from app.db.apply_sql import load_all_migration_statements, load_migration_statements


def test_migration_001_splits_into_statements() -> None:
    stmts = load_migration_statements("001_initial.sql")
    assert len(stmts) >= 10
    joined = "\n".join(stmts)
    assert "CREATE TABLE users" in joined
    assert "CREATE TABLE webhook_secrets" in joined
    assert "CREATE TYPE user_role" in joined


@pytest.mark.asyncio
async def test_migrations_apply_to_database() -> None:
    if os.getenv("RUN_DB_MIGRATION_TESTS") != "1":
        pytest.skip("Set RUN_DB_MIGRATION_TESTS=1 and TEST_DATABASE_URL to run destructive DB test")

    url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL or DATABASE_URL required")

    import asyncpg

    conn = await asyncpg.connect(url)
    try:
        await conn.execute("DROP SCHEMA IF EXISTS public CASCADE")
        await conn.execute("CREATE SCHEMA public")
        # Restore default grants (superuser DBs)
        await conn.execute("GRANT ALL ON SCHEMA public TO PUBLIC")

        for stmt in load_all_migration_statements():
            await conn.execute(stmt)

        rows = await conn.fetch(
            """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
            """
        )
        names = {r["tablename"] for r in rows}
        expected = {
            "users",
            "user_integration_settings",
            "platform_settings",
            "usage_counters",
            "ioc_jobs",
            "ioc_job_items",
            "activity_log",
            "webhook_secrets",
            "misp_explorer_cache",
        }
        assert expected == names
    finally:
        await conn.close()
