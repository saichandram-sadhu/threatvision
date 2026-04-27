"""Profile routes (internal JWT + pool overrides)."""

from __future__ import annotations

from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.auth.internal_jwt import (
    InternalUser,
    create_internal_token,
    get_current_internal_user as get_internal_user_dep,
)
from app.config import get_settings
from app.deps import get_pool
from app.main import create_application


class _FakePoolProfile:
    async def fetchrow(self, query: str, *args: object):
        if "FROM users" in query and "WHERE id = $1" in query and "usage_counters" not in query:
            return {
                "email": "u@example.com",
                "role": "USER",
                "api_key_prefix": "tv_test",
                "api_key_hash": "x",
                "daily_limit": 100,
                "unlimited": False,
                "banned": False,
            }
        return None

    async def fetchval(self, query: str, *args: object):
        if "usage_counters" in query and "SUM" in query:
            return 42
        if "usage_counters" in query:
            return 3
        if "SELECT banned" in query:
            return False
        return None

    async def fetch(self, query: str, *args: object):
        if "activity_log" in query:
            return [
                {
                    "ioc_snippet": "192.0.2.1",
                    "verdict": "MALICIOUS",
                    "created_at": datetime(2026, 3, 28, tzinfo=timezone.utc),
                }
            ]
        return []

    async def execute(self, *args: object, **kwargs: object) -> None:
        pass


def test_me_profile_ok() -> None:
    get_settings.cache_clear()
    app = create_application()

    async def fake_pool():
        return _FakePoolProfile()

    async def fake_user():
        return InternalUser(user_id="11111111-1111-1111-1111-111111111111", role="USER")

    app.dependency_overrides[get_pool] = fake_pool
    app.dependency_overrides[get_internal_user_dep] = fake_user
    token = create_internal_token("11111111-1111-1111-1111-111111111111", "USER")
    try:
        with TestClient(app) as client:
            r = client.get("/me/profile", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        body = r.json()
        assert body["email"] == "u@example.com"
        assert "tv_test" in body["api_key_masked"]
        assert body["has_api_key"] is True
        assert body["usage_last_7d"] == 42
        assert len(body["recent_activity"]) == 1
    finally:
        app.dependency_overrides.clear()


def test_me_regenerate_ok() -> None:
    get_settings.cache_clear()
    app = create_application()

    class P(_FakePoolProfile):
        async def fetchval(self, query: str, *args: object):
            if "SELECT banned" in query:
                return False
            return await super().fetchval(query, *args)

    async def fake_pool():
        return P()

    async def fake_user():
        return InternalUser(user_id="11111111-1111-1111-1111-111111111111", role="USER")

    app.dependency_overrides[get_pool] = fake_pool
    app.dependency_overrides[get_internal_user_dep] = fake_user
    token = create_internal_token("11111111-1111-1111-1111-111111111111", "USER")
    try:
        with TestClient(app) as client:
            r = client.post("/me/regenerate-api-key", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        body = r.json()
        assert "apiKey" in body
        assert "apiKeyPrefix" in body
        assert len(body["apiKey"]) > 20
    finally:
        app.dependency_overrides.clear()
