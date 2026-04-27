"""Sync ThreatVision platform/user MISP using MISP MySQL `users.authkey` (legacy/compatible)."""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path

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


def _upsert_dotenv(path: Path, updates: dict[str, str]) -> None:
    lines = path.read_text(encoding="utf-8-sig").splitlines() if path.is_file() else []
    out: list[str] = []
    seen: set[str] = set()
    for line in lines:
        s = line.strip()
        if s and not s.startswith("#") and "=" in s:
            k, _, _ = s.partition("=")
            k = k.strip()
            if k in updates:
                out.append(f"{k}={updates[k]}")
                seen.add(k)
                continue
        out.append(line)
    for k, v in updates.items():
        if k not in seen:
            out.append(f"{k}={v}")
    path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


def _fetch_misp_user_authkey() -> str:
    container = os.environ.get("MISP_DOCKER_DB_CONTAINER", "misp-db-1").strip()
    mysql_user = os.environ.get("MISP_DOCKER_MYSQL_USER", "misp").strip()
    mysql_pass = os.environ.get("MISP_DOCKER_MYSQL_PASSWORD", "example").strip()
    database = os.environ.get("MISP_DOCKER_MYSQL_DATABASE", "misp").strip()
    admin_email = os.environ.get("MISP_DOCKER_ADMIN_EMAIL", "admin@admin.test").strip()
    sql = (
        "SELECT authkey FROM users WHERE email = '"
        + admin_email.replace("'", "''")
        + "' AND authkey IS NOT NULL AND authkey != '' LIMIT 1"
    )
    cmd = [
        "docker",
        "exec",
        container,
        "mysql",
        "-u" + mysql_user,
        "-p" + mysql_pass,
        database,
        "-N",
        "-B",
        "-e",
        sql,
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError((out.stderr or out.stdout or "mysql failed").strip()[:400])
    key = (out.stdout or "").strip()
    if not key:
        raise RuntimeError("No users.authkey found in MISP MySQL")
    return key


async def main() -> int:
    _load_dotenv(_BACKEND / ".env")
    misp_url = (os.environ.get("PLATFORM_MISP_URL") or "https://127.0.0.1").strip()
    key = _fetch_misp_user_authkey()

    from app.config import get_settings
    from app.db.conn_params import connect_pg
    from app.services.crypto import encrypt_secret

    get_settings.cache_clear()
    db_url = get_settings().database_url or os.environ.get("DATABASE_URL")
    conn = await connect_pg(db_url)
    try:
        ct = encrypt_secret(key)
        await conn.execute(
            """
            UPDATE platform_settings
            SET misp_fallback_url = $1,
                misp_fallback_api_key_ciphertext = $2,
                updated_at = NOW()
            WHERE id = 1
            """,
            misp_url,
            ct,
        )
    finally:
        await conn.close()

    _upsert_dotenv(
        _BACKEND / ".env",
        {
            "PLATFORM_MISP_URL": misp_url,
            "PLATFORM_MISP_API_KEY": key,
        },
    )
    print("Synced platform MISP from MISP users.authkey into DB + backend/.env.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
