"""Restart not required — hits running API. Save VT slot + verify Analyze sees a key (not missing_api_key)."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import httpx

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))


def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        k, v = k.strip(), v.strip()
        if k and v:
            os.environ[k] = v


async def main() -> int:
    _load_dotenv(_BACKEND / ".env")
    base = (os.environ.get("VERIFY_API_BASE_URL") or "http://127.0.0.1:8003").rstrip("/")
    svc = (os.environ.get("BFF_SERVICE_KEY") or "").strip()
    if not svc:
        print("BFF_SERVICE_KEY missing", file=sys.stderr)
        return 1

    vt_key = (os.environ.get("THREATVISION_VT_API_KEY") or "").strip()
    if not vt_key:
        import secrets as _secrets

        vt_key = _secrets.token_hex(32)
        print(
            "THREATVISION_VT_API_KEY not set — using random 64-char placeholder "
            "(Analyze will call VT; expect 401/unavailable, not missing_api_key).",
        )

    from app.config import get_settings
    from app.db.conn_params import connect_pg

    get_settings.cache_clear()
    db_url = get_settings().database_url or os.environ["DATABASE_URL"]
    conn = await connect_pg(db_url)
    try:
        row = await conn.fetchrow(
            """
            SELECT id::text AS id, role::text AS role
            FROM users WHERE lower(email) = lower($1) LIMIT 1
            """,
            "admin@threatvision.dev",
        )
        if not row:
            print("admin@threatvision.dev not found", file=sys.stderr)
            return 1
        uid, role = row["id"], row["role"]
    finally:
        await conn.close()

    async with httpx.AsyncClient(timeout=120.0) as c:
        ex = await c.post(
            f"{base}/internal/auth/exchange",
            headers={"Content-Type": "application/json", "X-Service-Key": svc},
            json={"user_id": uid, "role": role},
        )
        if ex.status_code != 200:
            print("exchange failed", ex.status_code, ex.text[:400], file=sys.stderr)
            return 1
        token = ex.json()["access_token"]
        h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        put = await c.put(
            f"{base}/settings/integrations",
            headers=h,
            json={"secrets": {"virustotal": vt_key}, "source_toggles": {}},
        )
        if put.status_code != 200:
            print("PUT integrations failed", put.status_code, put.text[:600], file=sys.stderr)
            return 1
        put_body = put.json()
        slots = put_body.get("saved_secret_slots") or []
        print("PUT ok saved_secret_slots:", json.dumps(slots))

        getg = await c.get(f"{base}/settings/integrations", headers={"Authorization": f"Bearer {token}"})
        if getg.status_code != 200:
            print("GET integrations failed", getg.status_code, file=sys.stderr)
            return 1
        sources = getg.json().get("sources") or []
        vt = next((x for x in sources if x.get("id") == "virustotal"), None)
        print("GET virustotal configured:", vt.get("configured") if vt else None)

        an = await c.post(
            f"{base}/ioc/analyze",
            headers=h,
            json={"ioc": "8.8.8.8"},
        )
        if an.status_code != 200:
            print("analyze failed", an.status_code, an.text[:400], file=sys.stderr)
            return 1
        srcs = an.json().get("sources") or []
        vtr = next((x for x in srcs if x.get("id") == "virustotal"), None)
        st = vtr.get("status") if vtr else None
        ec = vtr.get("errorCode") if vtr else None
        print("Analyze virustotal status:", st, "errorCode:", ec)

    if "virustotal" not in slots:
        print("expected virustotal in saved_secret_slots", file=sys.stderr)
        return 1
    if st == "not_configured" and ec == "missing_api_key":
        print("still not_configured / missing_api_key", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
