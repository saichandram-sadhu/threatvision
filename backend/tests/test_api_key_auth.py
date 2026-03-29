"""API key HMAC and /v1/me dependency."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient

from app.auth.api_key import compute_api_key_hash, generate_api_key
from app.config import get_settings
from app.deps import get_pool
from app.main import app


def test_compute_api_key_hash_stable() -> None:
    pepper = "pepper-value-for-unit-test-only-32chars!!"
    h1 = compute_api_key_hash("same-key", pepper)
    h2 = compute_api_key_hash("same-key", pepper)
    assert h1 == h2
    assert h1 != compute_api_key_hash("other-key", pepper)


def test_generate_api_key_prefix() -> None:
    pepper = os.environ["API_KEY_PEPPER"]
    plain, digest, prefix = generate_api_key(pepper)
    assert len(plain) == 36
    assert plain.count("-") == 4
    assert len(prefix) == 8
    assert digest == compute_api_key_hash(plain, pepper)


def test_v1_me_with_pool_override() -> None:
    settings = get_settings()
    plain, digest, _ = generate_api_key(settings.api_key_pepper)
    row = {
        "id": "00000000-0000-0000-0000-000000000099",
        "email": "api@example.com",
        "role": "USER",
        "banned": False,
    }

    class FakePool:
        async def fetchrow(self, query: str, d: str):
            if d == digest:
                return row
            return None

    async def override_pool():
        return FakePool()

    app.dependency_overrides[get_pool] = override_pool
    try:
        with TestClient(app) as client:
            r = client.get("/v1/me", headers={"Authorization": f"Bearer {plain}"})
        assert r.status_code == 200
        assert r.json() == {
            "user_id": "00000000-0000-0000-0000-000000000099",
            "email": "api@example.com",
            "role": "USER",
        }
    finally:
        app.dependency_overrides.clear()


def test_v1_me_rejects_bad_key_with_pool_override() -> None:
    settings = get_settings()

    class FakePool:
        async def fetchrow(self, query: str, d: str):
            return None

    async def override_pool():
        return FakePool()

    app.dependency_overrides[get_pool] = override_pool
    try:
        with TestClient(app) as client:
            r = client.get(
                "/v1/me",
                headers={"Authorization": "Bearer 00000000-0000-0000-0000-000000000000"},
            )
        assert r.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_v1_me_503_when_pool_none() -> None:
    """No DATABASE_URL → pool unset → get_pool raises 503."""

    class AppWithNoPool:
        pass

    # Use fresh TestClient with app that has pool=None on state
    from contextlib import asynccontextmanager

    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    from app.routers import internal, v1_me

    @asynccontextmanager
    async def empty_lifespan(a: FastAPI):
        a.state.pool = None
        yield

    mini = FastAPI(lifespan=empty_lifespan)
    s = get_settings()
    mini.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_origin_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    mini.include_router(internal.router)
    mini.include_router(v1_me.router)

    settings = get_settings()
    plain, _, _ = generate_api_key(settings.api_key_pepper)

    with TestClient(mini) as client:
        r = client.get("/v1/me", headers={"Authorization": f"Bearer {plain}"})
    assert r.status_code == 503
