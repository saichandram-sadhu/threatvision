"""Registration throttle helpers and optional DB integration."""

from __future__ import annotations

import os
import uuid

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.config import get_settings
from app.db.apply_sql import load_all_migration_statements
from app.db.conn_params import connect_pg
from app.main import create_application
from app.services.auth.register_throttle import client_ip_from_request, enforce_registration_throttle


def test_client_ip_from_forwarded_header() -> None:
    scope = {
        "type": "http",
        "headers": [(b"x-forwarded-for", b"203.0.113.10, 10.0.0.1")],
        "client": ("127.0.0.1", 12345),
    }
    from starlette.requests import Request

    req = Request(scope)
    assert client_ip_from_request(req) == "203.0.113.10"


def test_client_ip_fallback_to_client_host() -> None:
    scope = {"type": "http", "headers": [], "client": ("192.0.2.1", 80)}
    from starlette.requests import Request

    req = Request(scope)
    assert client_ip_from_request(req) == "192.0.2.1"


@pytest.mark.asyncio
async def test_enforce_registration_throttle_blocks_after_limit() -> None:
    url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    if os.getenv("RUN_DB_MIGRATION_TESTS") != "1" or not url:
        pytest.skip("Set RUN_DB_MIGRATION_TESTS=1 and DATABASE_URL")

    conn = await connect_pg(url)
    try:
        await conn.execute("DROP SCHEMA IF EXISTS public CASCADE")
        await conn.execute("CREATE SCHEMA public")
        await conn.execute("GRANT ALL ON SCHEMA public TO PUBLIC")
        for stmt in load_all_migration_statements():
            await conn.execute(stmt)
    finally:
        await conn.close()

    import asyncpg

    pool = await asyncpg.create_pool(url, min_size=1, max_size=2)
    try:
        email = f"throttle-{uuid.uuid4().hex}@example.com"
        window_hit = False
        for i in range(25):
            try:
                await enforce_registration_throttle(
                    pool,
                    client_ip="198.51.100.50",
                    email_normalized=email,
                    ip_max_per_hour=5,
                    email_max_per_hour=100,
                )
            except HTTPException as e:
                assert e.status_code == 429
                window_hit = True
                break
        assert window_hit, "expected 429 after exceeding IP limit"
    finally:
        await pool.close()


@pytest.mark.asyncio
async def test_register_endpoint_429_when_ip_bucket_exceeded(monkeypatch: pytest.MonkeyPatch) -> None:
    url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    if os.getenv("RUN_DB_MIGRATION_TESTS") != "1" or not url:
        pytest.skip("Set RUN_DB_MIGRATION_TESTS=1 and DATABASE_URL")

    conn = await connect_pg(url)
    try:
        await conn.execute("DROP SCHEMA IF EXISTS public CASCADE")
        await conn.execute("CREATE SCHEMA public")
        await conn.execute("GRANT ALL ON SCHEMA public TO PUBLIC")
        for stmt in load_all_migration_statements():
            await conn.execute(stmt)
    finally:
        await conn.close()

    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("REGISTER_IP_MAX_PER_HOUR", "2")
    monkeypatch.setenv("REGISTER_EMAIL_MAX_PER_HOUR", "100")
    get_settings.cache_clear()
    fresh_app = create_application()

    with TestClient(fresh_app) as client:
        for i in range(2):
            r = client.post(
                "/auth/register",
                json={
                    "email": f"reg-{uuid.uuid4().hex[:10]}@example.com",
                    "password": "longpassword1",
                },
            )
            assert r.status_code == 201, r.text
        r3 = client.post(
            "/auth/register",
            json={"email": f"reg-{uuid.uuid4().hex[:10]}@example.com", "password": "longpassword1"},
        )
        assert r3.status_code == 429
