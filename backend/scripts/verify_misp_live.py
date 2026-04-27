"""Live check: resolve MISP for a user (same as API) and build explorer snapshot. No secrets printed."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

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
    from app.config import get_settings
    from app.db.conn_params import connect_pg
    from app.services.misp.explorer import build_explorer_snapshot
    from app.services.misp.resolve import resolve_misp_for_user

    get_settings.cache_clear()
    db_url = get_settings().database_url or os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL missing", file=sys.stderr)
        return 1

    email = (os.environ.get("MISP_VERIFY_USER_EMAIL") or "admin@threatvision.dev").strip()

    conn = await connect_pg(db_url)
    try:
        row = await conn.fetchrow(
            "SELECT id::text AS id FROM users WHERE lower(email) = lower($1) LIMIT 1",
            email,
        )
        if not row:
            print(f"User not found: {email}", file=sys.stderr)
            return 1
        user_id = row["id"]
        url, _key, tag = await resolve_misp_for_user(conn, user_id)
        if not url or not _key:
            print("resolve_misp_for_user: no URL/key (configure platform or user MISP).", file=sys.stderr)
            return 1

        snap = await build_explorer_snapshot(url, _key, resolution=tag)
        out = {
            "user_email": email,
            "resolution": snap.resolution,
            "base_url": snap.base_url,
            "connected": snap.connected,
            "misp_version": snap.misp_version,
            "feeds_count": len(snap.feeds),
            "servers_count": len(snap.servers),
            "taxonomies_count": len(snap.taxonomies),
            "sync_indicator": snap.sync_indicator,
            "stats_total_events": snap.stats.total_events,
            "source_errors": snap.source_errors or {},
        }
        print(json.dumps(out, indent=2))
        if not snap.connected and snap.source_errors:
            return 1
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
