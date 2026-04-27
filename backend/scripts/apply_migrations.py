"""Apply all app/db/migrations/*.sql to DATABASE_URL (asyncpg)."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_ROOT))

from app.db.apply_sql import load_all_migration_statements  # noqa: E402
from app.db.conn_params import connect_pg  # noqa: E402


def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip()
        if k and v:
            os.environ[k] = v


async def main() -> None:
    _load_dotenv(_BACKEND_ROOT / ".env")
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL missing. Create backend/.env or export DATABASE_URL.", file=sys.stderr)
        sys.exit(1)
    stmts = load_all_migration_statements()
    conn = await connect_pg(url)
    try:
        for i, stmt in enumerate(stmts, 1):
            await conn.execute(stmt)
            print(f"OK {i}/{len(stmts)}")
    finally:
        await conn.close()
    print("All migrations applied.")


if __name__ == "__main__":
    asyncio.run(main())
