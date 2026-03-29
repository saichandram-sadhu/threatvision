"""SIEM webhook HMAC + bearer verification."""

from __future__ import annotations

import hashlib
import hmac
import time

import pytest
from fastapi import HTTPException

from app.auth.api_key import compute_api_key_hash
from app.config import Settings
from app.services.siem.webhook_verify import (
    WebhookEndpointRow,
    assert_timestamp_fresh,
    authenticate_webhook,
    verify_hmac_body,
)


def _settings() -> Settings:
    return Settings(
        internal_jwt_secret="test-jwt-secret-min-32-chars-long!!",
        bff_service_key="bff-test-key-min-length-ok!!!!!",
        api_key_pepper="test-pepper-webhook",
        superadmin_email="admin@example.com",
    )


def test_verify_hmac_body_roundtrip() -> None:
    secret = "shared-secret"
    body = b'{"alert":1}'
    ts = int(time.time())
    msg = f"{ts}.".encode("utf-8") + body
    sig = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    assert verify_hmac_body(secret, ts, body, sig)
    assert not verify_hmac_body(secret, ts, body, "deadbeef")


def test_assert_timestamp_fresh_rejects_stale() -> None:
    old = int(time.time()) - 99999
    with pytest.raises(HTTPException) as ei:
        assert_timestamp_fresh(old)
    assert ei.value.status_code == 401


def test_authenticate_path_only() -> None:
    s = _settings()
    row = WebhookEndpointRow(user_id="u1", secret_hash=None, hmac_optional=False)
    authenticate_webhook(
        row,
        s,
        webhook_secret_header=None,
        timestamp_header=None,
        signature_hex=None,
        body=b"{}",
    )


def test_authenticate_bearer_required() -> None:
    s = _settings()
    plain = "whsec_test"
    digest = compute_api_key_hash(plain, s.api_key_pepper)
    row = WebhookEndpointRow(user_id="u1", secret_hash=digest, hmac_optional=False)
    authenticate_webhook(
        row,
        s,
        webhook_secret_header=plain,
        timestamp_header=None,
        signature_hex=None,
        body=b"{}",
    )
    with pytest.raises(HTTPException) as ei:
        authenticate_webhook(
            row,
            s,
            webhook_secret_header="wrong",
            timestamp_header=None,
            signature_hex=None,
            body=b"{}",
        )
    assert ei.value.status_code == 401


def test_authenticate_hmac_mode() -> None:
    s = _settings()
    plain = "hmackey"
    digest = compute_api_key_hash(plain, s.api_key_pepper)
    row = WebhookEndpointRow(user_id="u1", secret_hash=digest, hmac_optional=True)
    body = b'{"x":1}'
    ts = int(time.time())
    sig = hmac.new(
        plain.encode("utf-8"),
        f"{ts}.".encode("utf-8") + body,
        hashlib.sha256,
    ).hexdigest()
    authenticate_webhook(
        row,
        s,
        webhook_secret_header=plain,
        timestamp_header=str(ts),
        signature_hex=sig,
        body=body,
    )
