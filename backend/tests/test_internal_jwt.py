"""Internal JWT creation and validation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import HTTPException

from app.auth.internal_jwt import (
    ALGORITHM,
    TOKEN_TYPE,
    create_internal_token,
    decode_internal_token,
)
from app.config import get_settings


def test_create_and_decode_roundtrip() -> None:
    token = create_internal_token("user-uuid-1", "ADMIN")
    user = decode_internal_token(token)
    assert user.user_id == "user-uuid-1"
    assert user.role == "ADMIN"


def test_decode_rejects_wrong_typ() -> None:
    cfg = get_settings()
    payload = {
        "sub": "u",
        "role": "USER",
        "typ": "wrong",
        "iat": int(datetime.now(tz=UTC).timestamp()),
        "exp": datetime.now(tz=UTC) + timedelta(minutes=5),
    }
    token = jwt.encode(payload, cfg.internal_jwt_secret, algorithm=ALGORITHM)
    with pytest.raises(HTTPException) as exc:
        decode_internal_token(token)
    assert exc.value.status_code == 401


def test_decode_rejects_expired() -> None:
    cfg = get_settings()
    payload = {
        "sub": "u",
        "role": "USER",
        "typ": TOKEN_TYPE,
        "iat": 1,
        "exp": datetime.now(tz=UTC) - timedelta(minutes=5),
    }
    token = jwt.encode(payload, cfg.internal_jwt_secret, algorithm=ALGORITHM)
    with pytest.raises(HTTPException) as exc:
        decode_internal_token(token)
    assert exc.value.status_code == 401
