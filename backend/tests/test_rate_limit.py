"""Unit tests for Postgres daily rate limit (no real DB)."""

from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException

from app.services.rate_limit import check_and_increment_daily


class _AsyncCtx:
    def __init__(self, value):
        self._value = value

    async def __aenter__(self):
        return self._value

    async def __aexit__(self, *args):
        return False


class FakeConn:
    """Minimal asyncpg connection stub: ``transaction`` + ``fetchrow`` + ``execute``."""

    def __init__(self, user_rows: list[dict | None], usage_rows: list[dict | None]) -> None:
        self._user_rows = list(user_rows)
        self._usage_rows = list(usage_rows)
        self.executes: list[tuple[str, tuple]] = []

    def transaction(self):
        return _AsyncCtx(self)

    async def fetchrow(self, query: str, *args):  # noqa: ANN001
        q = query.strip().split()[0].upper()
        if "FROM users" in query:
            if not self._user_rows:
                raise RuntimeError("unexpected user fetchrow")
            return self._user_rows.pop(0)
        if "FROM usage_counters" in query:
            if not self._usage_rows:
                raise RuntimeError("unexpected usage fetchrow")
            return self._usage_rows.pop(0)
        raise AssertionError(f"unexpected query: {query[:80]}")

    async def execute(self, query: str, *args):  # noqa: ANN001
        self.executes.append((query, args))


class FakePool:
    def __init__(self, conn: FakeConn) -> None:
        self._conn = conn

    def acquire(self):
        return _AsyncCtx(self._conn)


@pytest.mark.asyncio
async def test_rate_limit_user_not_found() -> None:
    uid = uuid.uuid4()
    conn = FakeConn([None], [])
    with pytest.raises(HTTPException) as ei:
        await check_and_increment_daily(FakePool(conn), uid)
    assert ei.value.status_code == 401


@pytest.mark.asyncio
async def test_rate_limit_banned() -> None:
    uid = uuid.uuid4()
    conn = FakeConn([{"daily_limit": 10, "unlimited": False, "banned": True}], [])
    with pytest.raises(HTTPException) as ei:
        await check_and_increment_daily(FakePool(conn), uid)
    assert ei.value.status_code == 403


@pytest.mark.asyncio
async def test_rate_limit_unlimited_no_counter_write() -> None:
    uid = uuid.uuid4()
    conn = FakeConn([{"daily_limit": 1, "unlimited": True, "banned": False}], [])
    await check_and_increment_daily(FakePool(conn), uid)
    assert conn.executes == []


@pytest.mark.asyncio
async def test_rate_limit_exceeded_429() -> None:
    uid = uuid.uuid4()
    conn = FakeConn(
        [{"daily_limit": 5, "unlimited": False, "banned": False}],
        [{"request_count": 5}],
    )
    with pytest.raises(HTTPException) as ei:
        await check_and_increment_daily(FakePool(conn), uid)
    assert ei.value.status_code == 429
    assert ei.value.detail["error"] == "rate_limit_exceeded"


@pytest.mark.asyncio
async def test_rate_limit_inserts_first_counter_row() -> None:
    uid = uuid.uuid4()
    conn = FakeConn(
        [{"daily_limit": 100, "unlimited": False, "banned": False}],
        [None],
    )
    await check_and_increment_daily(FakePool(conn), uid)
    assert len(conn.executes) == 1
    assert "INSERT INTO usage_counters" in conn.executes[0][0]


@pytest.mark.asyncio
async def test_rate_limit_increments_existing_row() -> None:
    uid = uuid.uuid4()
    conn = FakeConn(
        [{"daily_limit": 100, "unlimited": False, "banned": False}],
        [{"request_count": 3}],
    )
    await check_and_increment_daily(FakePool(conn), uid)
    assert len(conn.executes) == 1
    assert "UPDATE usage_counters" in conn.executes[0][0]
