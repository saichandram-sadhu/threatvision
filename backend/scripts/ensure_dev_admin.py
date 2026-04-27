"""Create or reset dev superadmin (admin / admin) — uses admin@threatvision.dev (.local breaks Pydantic EmailStr)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))

DEV_EMAIL = "admin@threatvision.dev"
LEGACY_EMAIL = "admin@tv.local"


def _load_dotenv(path: Path) -> None:
    import os

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
    import os

    _load_dotenv(_BACKEND / ".env")

    from app.auth.api_key import generate_api_key
    from app.config import get_settings
    from app.db.conn_params import connect_pg
    from app.services.passwords import hash_password

    get_settings.cache_clear()
    settings = get_settings()
    url = settings.database_url
    if not url:
        print("DATABASE_URL missing in backend/.env", file=sys.stderr)
        sys.exit(1)

    password = "admin"
    pwd_hash = hash_password(password)
    plain_key, key_hash, prefix = generate_api_key(settings.api_key_pepper)

    conn = await connect_pg(url)
    try:
        has_new = await conn.fetchval("SELECT id::text FROM users WHERE email = $1", DEV_EMAIL)
        has_old = await conn.fetchval("SELECT id::text FROM users WHERE email = $1", LEGACY_EMAIL)

        if has_new:
            await conn.execute(
                """
                UPDATE users
                SET password_hash = $2, role = 'SUPERADMIN', banned = FALSE
                WHERE email = $1
                """,
                DEV_EMAIL,
                pwd_hash,
            )
            print("Updated", DEV_EMAIL, "SUPERADMIN, password set.")
        elif has_old:
            await conn.execute(
                """
                UPDATE users
                SET email = $1, password_hash = $2, role = 'SUPERADMIN', banned = FALSE
                WHERE email = $3
                """,
                DEV_EMAIL,
                pwd_hash,
                LEGACY_EMAIL,
            )
            print("Migrated", LEGACY_EMAIL, "->", DEV_EMAIL, "SUPERADMIN, password set.")
        else:
            await conn.execute(
                """
                INSERT INTO users (email, password_hash, name, role, api_key_hash, api_key_prefix)
                VALUES ($1, $2, $3, 'SUPERADMIN', $4, $5)
                """,
                DEV_EMAIL,
                pwd_hash,
                "Dev Admin",
                key_hash,
                prefix,
            )
            print("Created", DEV_EMAIL, "SUPERADMIN. API key (save once):", plain_key)
    finally:
        await conn.close()

    creds = _BACKEND.parent / ".dev_login_credentials.txt"
    creds.write_text(
        "\n".join(
            [
                "ThreatVision dev login (quick)",
                "URL:      http://localhost:3001/login",
                "Email:    admin                    (shortcut — needs DEV_QUICK_ADMIN_LOGIN=true)",
                "   or:    admin@threatvision.dev",
                "Password: admin",
                "",
                "Restart FastAPI after pulling code so /auth/login matches (avoid 422 on .local).",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("Wrote", creds)


if __name__ == "__main__":
    asyncio.run(main())
