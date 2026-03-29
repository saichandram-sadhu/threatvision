"""Short-lived HS256 JWT for Next.js BFF → FastAPI (spec §2)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from app.config import Settings, get_settings, get_settings_dep

ALGORITHM = "HS256"
TOKEN_TYPE = "internal"

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class InternalUser:
    user_id: str
    role: str


def create_internal_token(
    user_id: str,
    role: str,
    *,
    settings: Settings | None = None,
) -> str:
    cfg = settings or get_settings()
    now = datetime.now(tz=UTC)
    exp = now + timedelta(minutes=cfg.internal_jwt_expire_minutes)
    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "typ": TOKEN_TYPE,
        "iat": int(now.timestamp()),
        "exp": exp,
    }
    return jwt.encode(payload, cfg.internal_jwt_secret, algorithm=ALGORITHM)


def decode_internal_token(token: str, *, settings: Settings | None = None) -> InternalUser:
    cfg = settings or get_settings()
    try:
        payload = jwt.decode(
            token,
            cfg.internal_jwt_secret,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub", "role", "typ"]},
        )
    except ExpiredSignatureError as e:
        raise HTTPException(status_code=401, detail="Token expired") from e
    except InvalidTokenError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e

    if payload.get("typ") != TOKEN_TYPE:
        raise HTTPException(status_code=401, detail="Invalid token type")

    sub = payload.get("sub")
    role = payload.get("role")
    if not isinstance(sub, str) or not isinstance(role, str):
        raise HTTPException(status_code=401, detail="Invalid token claims")

    return InternalUser(user_id=sub, role=role)


async def get_current_internal_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> InternalUser:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return decode_internal_token(creds.credentials, settings=settings)
