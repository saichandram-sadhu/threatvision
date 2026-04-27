"""Rotate MISP admin auth key via Docker, validate it, then sync ThreatVision DB + .env."""

from __future__ import annotations

import asyncio
import os
import re
import shlex
import subprocess
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


def _upsert_dotenv(path: Path, updates: dict[str, str]) -> None:
    lines = path.read_text(encoding="utf-8-sig").splitlines() if path.is_file() else []
    out: list[str] = []
    touched: set[str] = set()
    for line in lines:
        s = line.strip()
        if s and not s.startswith("#") and "=" in s:
            k, _, _ = s.partition("=")
            k = k.strip()
            if k in updates:
                out.append(f"{k}={updates[k]}")
                touched.add(k)
                continue
        out.append(line)
    for k, v in updates.items():
        if k not in touched:
            out.append(f"{k}={v}")
    path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


def _issue_key_from_cake() -> str:
    container = os.environ.get("MISP_DOCKER_MISP_CONTAINER", "misp-misp-core-1").strip()
    admin_email = os.environ.get("MISP_DOCKER_ADMIN_EMAIL", "admin@admin.test").strip()
    inner = (
        "cd /var/www/MISP/app && ./Console/cake user change_authkey "
        + shlex.quote(admin_email)
    )
    cmd = ["docker", "exec", container, "bash", "-lc", inner]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    text = (out.stdout or "") + "\n" + (out.stderr or "")
    m = re.search(
        r"(?:new key created|Authentication key changed to):\s*(\S+)",
        text,
        flags=re.IGNORECASE,
    )
    if not m:
        raise RuntimeError(f"Could not parse new key from cake output: {text[:500]}")
    return m.group(1).strip()


async def _validate_key(base_url: str, api_key: str) -> None:
    async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=30.0) as c:
        r = await c.get(
            base_url.rstrip("/") + "/feeds/index.json",
            headers={"Authorization": api_key, "Accept": "application/json"},
        )
        if r.status_code >= 400:
            raise RuntimeError(f"feeds/index.json failed: {r.status_code} {r.text[:200]}")


async def main() -> int:
    _load_dotenv(_BACKEND / ".env")
    base_url = (os.environ.get("PLATFORM_MISP_URL") or "https://127.0.0.1").strip()
    if not base_url:
        print("PLATFORM_MISP_URL missing", file=sys.stderr)
        return 1

    new_key = _issue_key_from_cake()
    await _validate_key(base_url, new_key)

    from app.config import get_settings
    from app.db.conn_params import connect_pg
    from app.services.crypto import encrypt_secret

    get_settings.cache_clear()
    db_url = get_settings().database_url or os.environ.get("DATABASE_URL")
    conn = await connect_pg(db_url)
    try:
        ct = encrypt_secret(new_key)
        await conn.execute(
            """
            UPDATE platform_settings
            SET misp_fallback_url = $1,
                misp_fallback_api_key_ciphertext = $2,
                updated_at = NOW()
            WHERE id = 1
            """,
            base_url,
            ct,
        )
    finally:
        await conn.close()

    _upsert_dotenv(
        _BACKEND / ".env",
        {
            "PLATFORM_MISP_URL": base_url,
            "PLATFORM_MISP_API_KEY": new_key,
        },
    )
    print("Rotated MISP API key, validated against /feeds/index.json, synced DB + backend/.env.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
