"""Dashboard stats + activity routes with dependency overrides."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi.testclient import TestClient

from app.auth.internal_jwt import (
    InternalUser,
    create_internal_token,
    get_current_internal_user as get_internal_user_dep,
)
from app.config import get_settings
from app.deps import get_pool
from app.main import create_application


class _FakePoolDashboard:
    async def fetchrow(self, query: str, *args: object):
        assert "activity_log" in query
        assert isinstance(args[0], UUID)
        return {
            "analyses_1d": 2,
            "analyses_7d": 5,
            "analyses_30d": 12,
            "analyses_all": 20,
        }

    async def fetch(self, query: str, *args: object):
        assert "activity_log" in query
        if "GROUP BY verdict" in query:
            return [
                {"verdict": "MALICIOUS", "count": 7},
                {"verdict": "CLEAN", "count": 5},
            ]
        if "ioc_snippet AS ip" in query:
            return [{"ip": "192.0.2.10", "count": 4}]
        return []


class _FakePoolActivity:
    async def fetchrow(self, *args, **kwargs):
        raise AssertionError("unexpected fetchrow")

    async def fetch(self, query: str, *args: object):
        assert "activity_log" in query
        return [
            {
                "id": UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
                "ioc_snippet": "192.0.2.1",
                "verdict": "MALICIOUS",
                "flagged_by": ["misp", "virustotal"],
                "created_at": datetime(2026, 3, 28, 12, 0, 0, tzinfo=timezone.utc),
            }
        ]


def test_dashboard_stats_ok() -> None:
    get_settings.cache_clear()
    app = create_application()

    async def fake_pool():
        return _FakePoolDashboard()

    async def fake_user():
        return InternalUser(user_id="11111111-1111-1111-1111-111111111111", role="USER")

    app.dependency_overrides[get_pool] = fake_pool
    app.dependency_overrides[get_internal_user_dep] = fake_user
    token = create_internal_token("11111111-1111-1111-1111-111111111111", "USER")
    try:
        with TestClient(app) as client:
            r = client.get("/stats/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        body = r.json()
        assert body["analyses_1d"] == 2
        assert body["analyses_all"] == 20
        assert len(body["verdict_distribution_30d"]) == 2
        assert body["top_ips_30d"][0]["ip"] == "192.0.2.10"
    finally:
        app.dependency_overrides.clear()


def test_activity_recent_ok() -> None:
    get_settings.cache_clear()
    app = create_application()

    async def fake_pool():
        return _FakePoolActivity()

    async def fake_user():
        return InternalUser(user_id="11111111-1111-1111-1111-111111111111", role="USER")

    app.dependency_overrides[get_pool] = fake_pool
    app.dependency_overrides[get_internal_user_dep] = fake_user
    token = create_internal_token("11111111-1111-1111-1111-111111111111", "USER")
    try:
        with TestClient(app) as client:
            r = client.get("/activity/recent?limit=10", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        body = r.json()
        assert len(body["items"]) == 1
        item = body["items"][0]
        assert item["ioc_snippet"] == "192.0.2.1"
        assert item["verdict"] == "MALICIOUS"
        names = {c["id"]: c["display_name"] for c in item["flagged_by"]}
        assert names["misp"] == "MISP"
        assert names["virustotal"] == "VirusTotal"
    finally:
        app.dependency_overrides.clear()
