"""Email/password registration and login (NextAuth credentials backend)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.auth.api_key import generate_api_key
from app.config import Settings, get_settings_dep
from app.deps import PoolDep
from app.services.passwords import hash_password, verify_password
from app.services.superadmin import maybe_promote_superadmin

router = APIRouter(tags=["auth"])


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)
    name: str | None = Field(default=None, max_length=255)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class RegisterOut(BaseModel):
    user_id: str
    email: str
    role: str
    api_key: str


class LoginOut(BaseModel):
    user_id: str
    email: str
    role: str


@router.post("/auth/register", response_model=RegisterOut, status_code=201)
async def register(
    body: RegisterIn,
    pool: PoolDep,
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> RegisterOut:
    email = body.email.strip().lower()
    taken = await pool.fetchval("SELECT 1 FROM users WHERE email = $1", email)
    if taken:
        raise HTTPException(status_code=409, detail="Email already registered")

    pwd_hash = hash_password(body.password)
    plain_key, key_hash, prefix = generate_api_key(settings.api_key_pepper)

    user_id = await pool.fetchval(
        """
        INSERT INTO users (email, password_hash, name, role, api_key_hash, api_key_prefix)
        VALUES ($1, $2, $3, 'USER', $4, $5)
        RETURNING id::text
        """,
        email,
        pwd_hash,
        body.name,
        key_hash,
        prefix,
    )
    return RegisterOut(user_id=user_id, email=email, role="USER", api_key=plain_key)


@router.post("/auth/login", response_model=LoginOut)
async def login(
    body: LoginIn,
    pool: PoolDep,
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> LoginOut:
    email = body.email.strip().lower()
    row = await pool.fetchrow(
        """
        SELECT id::text AS id, email, password_hash, role::text AS role, banned
        FROM users
        WHERE email = $1
        """,
        email,
    )
    if row is None or row["password_hash"] is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if row["banned"]:
        raise HTTPException(status_code=403, detail="Account disabled")
    if not verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    await maybe_promote_superadmin(
        pool,
        user_id=row["id"],
        email_normalized=email,
        settings=settings,
    )

    out = await pool.fetchrow(
        """
        SELECT id::text AS id, email, role::text AS role
        FROM users
        WHERE id = $1::uuid
        """,
        row["id"],
    )
    if out is None:
        raise HTTPException(status_code=500, detail="User missing after login")
    return LoginOut(user_id=out["id"], email=out["email"], role=out["role"])
