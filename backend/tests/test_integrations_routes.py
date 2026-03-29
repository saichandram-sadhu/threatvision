"""Integrations settings routes (dependency overrides)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.auth.internal_jwt import (
    InternalUser,
    create_internal_token,
    get_current_internal_user as get_internal_user_dep,
)
from app.config import get_settings
from app.deps import get_pool
from app.main import create_application


class _FakePoolGetIntegrations:
    async def fetchrow(self, query: str, *args: object):
        if "misp_base_url" in query and "source_toggles" not in query:
            return {"misp_base_url": "https://misp.example", "misp_api_key_ciphertext": "enc"}
        return {"source_toggles": {"virustotal": True}, "secrets_ciphertext": None}


class _FakePoolPutIntegrations:
    def __init__(self) -> None:
        self.executed = False

    async def fetchrow(self, query: str, *args: object):
        return None

    async def execute(self, *args: object, **kwargs: object) -> None:
        self.executed = True


def test_get_integrations_ok() -> None:
    get_settings.cache_clear()
    app = create_application()

    async def fake_pool():
        return _FakePoolGetIntegrations()

    async def fake_user():
        return InternalUser(user_id="11111111-1111-1111-1111-111111111111", role="USER")

    app.dependency_overrides[get_pool] = fake_pool
    app.dependency_overrides[get_internal_user_dep] = fake_user
    token = create_internal_token("11111111-1111-1111-1111-111111111111", "USER")
    try:
        with TestClient(app) as client:
            r = client.get("/settings/integrations", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        body = r.json()
        assert body["misp"]["base_url"] == "https://misp.example"
        assert body["misp"]["key_configured"] is True
        ids = {s["id"] for s in body["sources"]}
        assert "virustotal" in ids
        assert "misp" not in ids
    finally:
        app.dependency_overrides.clear()


def test_put_integrations_inserts() -> None:
    get_settings.cache_clear()
    app = create_application()
    pool = _FakePoolPutIntegrations()

    async def fake_pool():
        return pool

    async def fake_user():
        return InternalUser(user_id="11111111-1111-1111-1111-111111111111", role="USER")

    app.dependency_overrides[get_pool] = fake_pool
    app.dependency_overrides[get_internal_user_dep] = fake_user
    token = create_internal_token("11111111-1111-1111-1111-111111111111", "USER")
    try:
        with TestClient(app) as client:
            r = client.put(
                "/settings/integrations",
                headers={"Authorization": f"Bearer {token}"},
                json={"source_toggles": {"otx": False}},
            )
        assert r.status_code == 200
        assert pool.executed is True
    finally:
        app.dependency_overrides.clear()
