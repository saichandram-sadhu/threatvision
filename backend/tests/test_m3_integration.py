"""Auth, superadmin bootstrap, and rate limits — requires Postgres (destructive)."""

from __future__ import annotations

import os
import uuid

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.config import get_settings
from app.db.apply_sql import load_all_migration_statements
from app.main import create_application
from app.services.rate_limit import check_and_increment_daily


def _db_url() -> str | None:
    if os.getenv("RUN_DB_MIGRATION_TESTS") != "1":
        return None
    return os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")


@pytest.mark.asyncio
async def test_auth_superadmin_and_rate_limit_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    url = _db_url()
    if not url:
        pytest.skip("Set RUN_DB_MIGRATION_TESTS=1 and TEST_DATABASE_URL")

    import asyncpg

    conn = await asyncpg.connect(url)
    try:
        await conn.execute("DROP SCHEMA IF EXISTS public CASCADE")
        await conn.execute("CREATE SCHEMA public")
        await conn.execute("GRANT ALL ON SCHEMA public TO PUBLIC")
        for stmt in load_all_migration_statements():
            await conn.execute(stmt)
    finally:
        await conn.close()

    super_email = os.environ["SUPERADMIN_EMAIL"].strip().lower()
    other_email = f"user-{uuid.uuid4().hex[:8]}@example.com"

    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    fresh_app = create_application()

    with TestClient(fresh_app) as client:
        r = client.post(
            "/auth/register",
            json={"email": super_email, "password": "longpassword1", "name": "SA"},
        )
        assert r.status_code == 201
        body = r.json()
        assert body["role"] == "USER"
        api_key = body["api_key"]

        r2 = client.post(
            "/auth/login",
            json={"email": super_email, "password": "longpassword1"},
        )
        assert r2.status_code == 200
        assert r2.json()["role"] == "SUPERADMIN"

        r3 = client.post(
            "/auth/register",
            json={"email": other_email, "password": "longpassword1"},
        )
        assert r3.status_code == 201
        uid_other = r3.json()["user_id"]

        r4 = client.post(
            "/auth/login",
            json={"email": other_email, "password": "longpassword1"},
        )
        assert r4.status_code == 200
        assert r4.json()["role"] == "USER"

        conn2 = await asyncpg.connect(url)
        try:
            await conn2.execute(
                "UPDATE users SET role = 'SUPERADMIN' WHERE id = $1::uuid",
                uid_other,
            )
            await conn2.execute(
                "UPDATE users SET role = 'USER' WHERE email = $1",
                super_email,
            )
        finally:
            await conn2.close()

        r5 = client.post(
            "/auth/login",
            json={"email": super_email, "password": "longpassword1"},
        )
        assert r5.status_code == 200
        assert r5.json()["role"] == "USER"

        me = client.get("/v1/me", headers={"Authorization": f"Bearer {api_key}"})
        assert me.status_code == 200
        uid_super = me.json()["user_id"]

        conn3 = await asyncpg.connect(url)
        try:
            await conn3.execute(
                "UPDATE users SET daily_limit = 2 WHERE id = $1::uuid",
                uuid.UUID(uid_super),
            )
        finally:
            await conn3.close()

        pool = fresh_app.state.pool
        assert pool is not None
        u = uuid.UUID(uid_super)
        await check_and_increment_daily(pool, u)
        await check_and_increment_daily(pool, u)
        with pytest.raises(HTTPException) as exc:
            await check_and_increment_daily(pool, u)
        assert exc.value.status_code == 429

    get_settings.cache_clear()
