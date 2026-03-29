"""Superadmin admin routes — requires Postgres (same gate as test_m3_integration)."""

from __future__ import annotations

import os
import uuid

import pytest
from fastapi.testclient import TestClient

from app.auth.internal_jwt import create_internal_token
from app.config import get_settings
from app.db.apply_sql import load_all_migration_statements
from app.main import create_application


def _db_url() -> str | None:
    if os.getenv("RUN_DB_MIGRATION_TESTS") != "1":
        return None
    return os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")


@pytest.mark.asyncio
async def test_admin_superadmin_flow(monkeypatch: pytest.MonkeyPatch) -> None:
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
    other_email = f"u-{uuid.uuid4().hex[:8]}@example.com"

    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    fresh_app = create_application()

    with TestClient(fresh_app) as client:
        r = client.post(
            "/auth/register",
            json={"email": super_email, "password": "longpassword1", "name": "SA"},
        )
        assert r.status_code == 201
        sa_uid = r.json()["user_id"]

        lr = client.post(
            "/auth/login",
            json={"email": super_email, "password": "longpassword1"},
        )
        assert lr.status_code == 200
        assert lr.json()["role"] == "SUPERADMIN"

        r2 = client.post(
            "/auth/register",
            json={"email": other_email, "password": "longpassword1", "name": "U"},
        )
        assert r2.status_code == 201
        other_uid = r2.json()["user_id"]

        bad_tok = create_internal_token(other_uid, "USER")
        r403 = client.get("/admin/users", headers={"Authorization": f"Bearer {bad_tok}"})
        assert r403.status_code == 403

        bad_admin = create_internal_token(other_uid, "SUPERADMIN")
        r403b = client.get("/admin/users", headers={"Authorization": f"Bearer {bad_admin}"})
        assert r403b.status_code == 403

        sa_tok = create_internal_token(sa_uid, "SUPERADMIN")
        rlist = client.get("/admin/users", headers={"Authorization": f"Bearer {sa_tok}"})
        assert rlist.status_code == 200
        users = rlist.json()
        assert len(users) >= 2
        emails = {u["email"] for u in users}
        assert super_email in emails
        assert other_email in emails

        rp = client.patch(
            f"/admin/users/{other_uid}",
            headers={"Authorization": f"Bearer {sa_tok}"},
            json={"dailyLimit": 42, "unlimited": False},
        )
        assert rp.status_code == 200

        rkey = client.post(
            f"/admin/users/{other_uid}/regenerate-api-key",
            headers={"Authorization": f"Bearer {sa_tok}"},
        )
        assert rkey.status_code == 200
        new_key = rkey.json()["apiKey"]
        assert len(new_key) > 10

        me = client.get("/v1/me", headers={"Authorization": f"Bearer {new_key}"})
        assert me.status_code == 200
        assert me.json()["user_id"] == other_uid

        gm = client.get("/admin/platform/misp", headers={"Authorization": f"Bearer {sa_tok}"})
        assert gm.status_code == 200
        assert gm.json()["hasMispFallbackApiKey"] is False

        pm = client.put(
            "/admin/platform/misp",
            headers={"Authorization": f"Bearer {sa_tok}"},
            json={
                "misp_fallback_url": "https://misp.platform.example",
                "misp_fallback_api_key": "test-platform-key-12345678",
            },
        )
        assert pm.status_code == 200
        assert pm.json()["mispFallbackUrl"] == "https://misp.platform.example"
        assert pm.json()["hasMispFallbackApiKey"] is True

    get_settings.cache_clear()
