"""Hit running FastAPI: exchange internal JWT then GET /misp/explorer (end-to-end BFF path simulation)."""

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
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip()
        if k and v:
            os.environ[k] = v


async def main() -> int:
    _load_dotenv(_BACKEND / ".env")
    base = (os.environ.get("VERIFY_API_BASE_URL") or "http://127.0.0.1:8002").rstrip("/")
    key = (os.environ.get("BFF_SERVICE_KEY") or "").strip()
    if not key:
        print("BFF_SERVICE_KEY missing in .env", file=sys.stderr)
        return 1

    from app.config import get_settings
    from app.db.conn_params import connect_pg

    get_settings.cache_clear()
    db_url = get_settings().database_url or os.environ.get("DATABASE_URL")
    email = (os.environ.get("MISP_VERIFY_USER_EMAIL") or "admin@threatvision.dev").strip()

    conn = await connect_pg(db_url)
    try:
        row = await conn.fetchrow(
            """
            SELECT id::text AS id, role::text AS role
            FROM users WHERE lower(email) = lower($1) LIMIT 1
            """,
            email,
        )
        if not row:
            print(f"User not found: {email}", file=sys.stderr)
            return 1
        user_id, role = row["id"], row["role"]
    finally:
        await conn.close()

    async with httpx.AsyncClient(timeout=120.0) as client:
        ex = await client.post(
            f"{base}/internal/auth/exchange",
            headers={"Content-Type": "application/json", "X-Service-Key": key},
            json={"user_id": user_id, "role": role},
        )
        if ex.status_code != 200:
            print("exchange failed:", ex.status_code, ex.text[:500], file=sys.stderr)
            return 1
        token = ex.json().get("access_token")
        if not token:
            print("no access_token", file=sys.stderr)
            return 1

        r = await client.get(
            f"{base}/misp/explorer",
            headers={"Authorization": f"Bearer {token}"},
        )
        if r.status_code != 200:
            print("explorer failed:", r.status_code, r.text[:800], file=sys.stderr)
            return 1
        body = r.json()
        summary = {
            "api_base": base,
            "explorer_status": r.status_code,
            "resolution": body.get("resolution"),
            "connected": body.get("connected"),
            "misp_version": body.get("misp_version"),
            "feeds": len(body.get("feeds") or []),
        }
        print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
