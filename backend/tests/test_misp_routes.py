"""MISP HTTP routes (internal JWT + pool overrides)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.auth.internal_jwt import (
    InternalUser,
    create_internal_token,
    get_current_internal_user as get_internal_user_dep,
)
from app.config import get_settings
from app.deps import get_pool
from app.main import create_application


class _FakePoolUnconfigured:
    async def fetchrow(self, *args, **kwargs):
        return None

    async def execute(self, *args, **kwargs):
        return None


def test_misp_test_unconfigured_returns_ok_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLATFORM_MISP_URL", "")
    monkeypatch.setenv("PLATFORM_MISP_API_KEY", "")
    monkeypatch.setenv("THREATVISION_SKIP_LOCAL_ENV_MISP", "1")
    get_settings.cache_clear()
    app = create_application()

    async def fake_pool():
        return _FakePoolUnconfigured()

    async def fake_user():
        return InternalUser(user_id="11111111-1111-1111-1111-111111111111", role="USER")

    app.dependency_overrides[get_pool] = fake_pool
    app.dependency_overrides[get_internal_user_dep] = fake_user
    token = create_internal_token("11111111-1111-1111-1111-111111111111", "USER")
    try:
        with TestClient(app) as client:
            r = client.post(
                "/settings/misp/test",
                json={},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is False
        assert body["resolution"] == "none"
    finally:
        app.dependency_overrides.clear()


def test_misp_explorer_unconfigured_returns_400(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLATFORM_MISP_URL", "")
    monkeypatch.setenv("PLATFORM_MISP_API_KEY", "")
    monkeypatch.setenv("THREATVISION_SKIP_LOCAL_ENV_MISP", "1")
    get_settings.cache_clear()
    app = create_application()

    async def fake_pool():
        return _FakePoolUnconfigured()

    async def fake_user():
        return InternalUser(user_id="11111111-1111-1111-1111-111111111111", role="USER")

    app.dependency_overrides[get_pool] = fake_pool
    app.dependency_overrides[get_internal_user_dep] = fake_user
    token = create_internal_token("11111111-1111-1111-1111-111111111111", "USER")
    try:
        with TestClient(app) as client:
            r = client.get(
                "/misp/explorer",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 400
    finally:
        app.dependency_overrides.clear()
