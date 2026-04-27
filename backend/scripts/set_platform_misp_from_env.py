"""Write Docker/local MISP into platform_settings. Auto-resolves API key (TV DB, Docker MySQL, or MISP Cake)."""

from __future__ import annotations

import asyncio
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))


def _upsert_dotenv(path: Path, updates: dict[str, str]) -> None:
    """Merge key=value lines into .env (creates file if missing)."""
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    keys_done: set[str] = set()
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k, _, _ = stripped.partition("=")
            k = k.strip()
            if k in updates:
                out.append(f"{k}={updates[k]}")
                keys_done.add(k)
                continue
        out.append(line)
    for k, v in updates.items():
        if k not in keys_done:
            out.append(f"{k}={v}")
    path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


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


def _docker_fetch_allowed() -> bool:
    v = os.environ.get("MISP_DOCKER_FETCH_AUTHKEY", "true").strip().lower()
    return v not in ("0", "false", "no", "off")


def _cake_authkey_allowed() -> bool:
    v = os.environ.get("MISP_DOCKER_CAKE_AUTHKEY", "true").strip().lower()
    return v not in ("0", "false", "no", "off")


def _fetch_misp_authkey_from_mysql() -> str | None:
    """Legacy MISP: plain authkey in users table (often stale on 2.5+)."""
    if not _docker_fetch_allowed():
        return None
    container = os.environ.get("MISP_DOCKER_DB_CONTAINER", "misp-db-1").strip()
    mysql_user = os.environ.get("MISP_DOCKER_MYSQL_USER", "misp").strip()
    mysql_pass = os.environ.get("MISP_DOCKER_MYSQL_PASSWORD", "example").strip()
    database = os.environ.get("MISP_DOCKER_MYSQL_DATABASE", "misp").strip()
    admin_email = os.environ.get("MISP_DOCKER_ADMIN_EMAIL", "admin@admin.test").strip()
    if not all((container, mysql_user, mysql_pass, database, admin_email)):
        return None
    esc = admin_email.replace("\\", "\\\\").replace("'", "''")
    sql = (
        "SELECT authkey FROM users WHERE email = '"
        + esc
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
        "-e",
        sql,
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        if out.returncode != 0:
            return None
        lines = [x.strip() for x in out.stdout.strip().splitlines() if x.strip()]
        if not lines:
            return None
        candidate = lines[-1].strip()
        return candidate if len(candidate) >= 8 else None
    except (OSError, subprocess.SubprocessError):
        return None


def _cake_issue_fresh_authkey() -> str | None:
    """MISP 2.5+: create a new key via Cake (stored in auth_keys)."""
    if not _cake_authkey_allowed():
        return None
    container = os.environ.get("MISP_DOCKER_MISP_CONTAINER", "misp-misp-core-1").strip()
    admin_email = os.environ.get("MISP_DOCKER_ADMIN_EMAIL", "admin@admin.test").strip()
    if not container or not admin_email:
        return None
    inner = (
        "cd /var/www/MISP/app && ./Console/cake user change_authkey "
        + shlex.quote(admin_email)
    )
    cmd = ["docker", "exec", container, "bash", "-lc", inner]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        text = (out.stdout or "") + (out.stderr or "")
        m = re.search(
            r"new key created:\s*(\S+)",
            text,
            flags=re.IGNORECASE,
        )
        if m:
            return m.group(1).strip()
        if out.returncode != 0:
            print("cake user change_authkey:", text.strip()[:800], file=sys.stderr)
        return None
    except (OSError, subprocess.SubprocessError) as e:
        print("cake authkey failed:", e, file=sys.stderr)
        return None


async def _existing_key_from_tv(conn) -> str | None:
    from app.services.crypto import CryptoError, decrypt_secret

    row = await conn.fetchrow(
        """
        SELECT misp_fallback_api_key_ciphertext
        FROM platform_settings
        WHERE id = 1
        """,
    )
    if not row or not row["misp_fallback_api_key_ciphertext"]:
        return None
    try:
        return decrypt_secret(row["misp_fallback_api_key_ciphertext"])
    except CryptoError:
        return None


async def _ping_ok(url: str, key: str) -> bool:
    from app.services.misp.http import misp_ping_version

    try:
        await misp_ping_version(url, key)
        return True
    except Exception:
        return False


async def main() -> None:
    _load_dotenv(_BACKEND / ".env")

    from app.config import get_settings
    from app.db.conn_params import connect_pg
    from app.services.crypto import encrypt_secret
    from app.services.misp.resolve import normalize_misp_base_url

    get_settings.cache_clear()
    settings = get_settings()
    db_url = settings.database_url or os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL missing in backend/.env", file=sys.stderr)
        sys.exit(1)

    url = (os.environ.get("PLATFORM_MISP_URL") or "").strip()
    if not url:
        print("Set PLATFORM_MISP_URL (e.g. https://127.0.0.1).", file=sys.stderr)
        sys.exit(1)
    normalized = normalize_misp_base_url(url)

    conn = await connect_pg(db_url)
    try:
        key = (os.environ.get("PLATFORM_MISP_API_KEY") or "").strip()
        if not key:
            key = (await _existing_key_from_tv(conn) or "").strip()
        if not key:
            key = (_fetch_misp_authkey_from_mysql() or "").strip()

        if not key or not await _ping_ok(normalized, key):
            fresh = _cake_issue_fresh_authkey()
            if fresh:
                print("Issued new MISP API key via Docker (cake user change_authkey).")
                key = fresh

        if not key:
            print("Could not obtain a working MISP API key.", file=sys.stderr)
            sys.exit(1)

        if not await _ping_ok(normalized, key):
            print("MISP ping failed — check PLATFORM_MISP_URL and TLS (MISP_TLS_VERIFY=false for self-signed).", file=sys.stderr)
            sys.exit(1)

        ciphertext = encrypt_secret(key)
        await conn.execute(
            """
            UPDATE platform_settings
            SET misp_fallback_url = $1,
                misp_fallback_api_key_ciphertext = $2,
                updated_at = NOW()
            WHERE id = 1
            """,
            normalized,
            ciphertext,
        )
    finally:
        await conn.close()

    print("platform_settings: MISP fallback saved:", normalized)
    print("ThreatVision will use this MISP for users without personal MISP settings.")

    if os.environ.get("MISP_SKIP_WRITE_DOTENV", "").strip().lower() not in ("1", "true", "yes"):
        env_path = _BACKEND / ".env"
        _upsert_dotenv(
            env_path,
            {
                "PLATFORM_MISP_URL": normalized,
                "PLATFORM_MISP_API_KEY": key,
            },
        )
        print("Also wrote PLATFORM_MISP_URL + PLATFORM_MISP_API_KEY to backend/.env (restart uvicorn to pick up Settings).")


if __name__ == "__main__":
    asyncio.run(main())
