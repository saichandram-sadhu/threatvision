"""Copy platform MISP URL+key into admin@threatvision.dev user_integration_settings (Integrations UI)."""

from __future__ import annotations

import asyncio
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


async def main() -> None:
    _load_dotenv(_BACKEND / ".env")
    from app.db.conn_params import connect_pg
    from app.services.crypto import decrypt_secret, encrypt_secret

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL missing", file=sys.stderr)
        sys.exit(1)

    conn = await connect_pg(db_url)
    try:
        row = await conn.fetchrow(
            """
            SELECT misp_fallback_url, misp_fallback_api_key_ciphertext
            FROM platform_settings
            WHERE id = 1
            """,
        )
        if not row or not row["misp_fallback_url"] or not row["misp_fallback_api_key_ciphertext"]:
            print("No platform MISP row — run scripts/set_platform_misp_from_env.py first", file=sys.stderr)
            sys.exit(1)
        key_plain = decrypt_secret(row["misp_fallback_api_key_ciphertext"])
        url = row["misp_fallback_url"].strip()
        ct = encrypt_secret(key_plain)

        u = await conn.fetchrow(
            """
            SELECT id FROM users WHERE lower(email) = lower($1) LIMIT 1
            """,
            "admin@threatvision.dev",
        )
        if not u:
            print("admin@threatvision.dev not in users table", file=sys.stderr)
            sys.exit(1)
        uid = u["id"]
        await conn.execute(
            """
            INSERT INTO user_integration_settings (
                user_id, source_toggles, secrets_ciphertext,
                misp_base_url, misp_api_key_ciphertext, updated_at
            )
            VALUES ($1, '{}'::jsonb, NULL, $2, $3, NOW())
            ON CONFLICT (user_id) DO UPDATE SET
                misp_base_url = EXCLUDED.misp_base_url,
                misp_api_key_ciphertext = EXCLUDED.misp_api_key_ciphertext,
                updated_at = NOW()
            """,
            uid,
            url,
            ct,
        )
        print("Copied platform MISP into user_integration_settings for admin@threatvision.dev")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
