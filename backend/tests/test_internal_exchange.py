"""BFF internal auth exchange endpoint."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient

from app.auth.internal_jwt import decode_internal_token
from app.main import app


def test_exchange_rejects_missing_service_key() -> None:
    with TestClient(app) as client:
        r = client.post("/internal/auth/exchange", json={"user_id": "x", "role": "USER"})
        assert r.status_code == 401


def test_exchange_rejects_invalid_service_key() -> None:
    with TestClient(app) as client:
        r = client.post(
            "/internal/auth/exchange",
            json={"user_id": "x", "role": "USER"},
            headers={"X-Service-Key": "not-the-configured-bff-service-key-12345"},
        )
        assert r.status_code == 401


def test_exchange_returns_valid_jwt() -> None:
    key = os.environ["BFF_SERVICE_KEY"]
    with TestClient(app) as client:
        r = client.post(
            "/internal/auth/exchange",
            json={"user_id": "11111111-1111-1111-1111-111111111111", "role": "USER"},
            headers={"X-Service-Key": key},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert "access_token" in body
    assert body["expires_in"] > 0

    user = decode_internal_token(body["access_token"])
    assert user.user_id == "11111111-1111-1111-1111-111111111111"
    assert user.role == "USER"
