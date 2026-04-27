"""BFF internal auth exchange endpoint."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.auth.internal_jwt import decode_internal_token
from app.main import app


def test_exchange_rejects_missing_service_key() -> None:
    with TestClient(app) as client:
        r = client.post(
            "/internal/auth/exchange",
            json={"user_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", "role": "USER"},
        )
        assert r.status_code == 401


def test_exchange_rejects_invalid_service_key() -> None:
    with TestClient(app) as client:
        r = client.post(
            "/internal/auth/exchange",
            json={"user_id": "11111111-1111-1111-1111-111111111111", "role": "USER"},
            headers={"X-Service-Key": "not-the-configured-bff-service-key-12345"},
        )
        assert r.status_code == 401


def test_exchange_returns_valid_jwt_when_user_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    uid = "11111111-1111-1111-1111-111111111111"
    mock_pool = MagicMock()
    mock_pool.fetchrow = AsyncMock(
        return_value={"id": uid, "role": "USER", "banned": False},
    )

    async def fake_get_pool(_request):
        return mock_pool

    monkeypatch.setattr("app.routers.internal.get_pool", fake_get_pool)
    key = os.environ["BFF_SERVICE_KEY"]
    with TestClient(app) as client:
        r = client.post(
            "/internal/auth/exchange",
            json={"user_id": uid, "role": "USER"},
            headers={"X-Service-Key": key},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert "access_token" in body
    assert body["expires_in"] > 0

    user = decode_internal_token(body["access_token"])
    assert user.user_id == uid
    assert user.role == "USER"


def test_exchange_rejects_unknown_user(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_pool = MagicMock()
    mock_pool.fetchrow = AsyncMock(return_value=None)

    async def fake_get_pool(_request):
        return mock_pool

    monkeypatch.setattr("app.routers.internal.get_pool", fake_get_pool)
    key = os.environ["BFF_SERVICE_KEY"]
    with TestClient(app) as client:
        r = client.post(
            "/internal/auth/exchange",
            json={"user_id": "22222222-2222-2222-2222-222222222222", "role": "USER"},
            headers={"X-Service-Key": key},
        )
    assert r.status_code == 403


def test_exchange_rejects_role_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    uid = "33333333-3333-3333-3333-333333333333"
    mock_pool = MagicMock()
    mock_pool.fetchrow = AsyncMock(
        return_value={"id": uid, "role": "USER", "banned": False},
    )

    async def fake_get_pool(_request):
        return mock_pool

    monkeypatch.setattr("app.routers.internal.get_pool", fake_get_pool)
    key = os.environ["BFF_SERVICE_KEY"]
    with TestClient(app) as client:
        r = client.post(
            "/internal/auth/exchange",
            json={"user_id": uid, "role": "ADMIN"},
            headers={"X-Service-Key": key},
        )
    assert r.status_code == 403
