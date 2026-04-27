"""Set password for a user by email (local dev). Reads backend/.env for DATABASE_URL."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))

from app.db.conn_params import connect_pg  # noqa: E402
from app.services.passwords import hash_password  # noqa: E402


def _load_env() -> dict[str, str]:
    p = _BACKEND / ".env"
    out: dict[str, str] = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        out[k.strip()] = v.strip()
    return out


async def main() -> None:
    env = _load_env()
    url = env.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL missing in backend/.env", file=sys.stderr)
        sys.exit(1)
    email = (os.environ.get("RESET_EMAIL") or env.get("SUPERADMIN_EMAIL") or "").strip().lower()
    if not email:
        print("No email: set SUPERADMIN_EMAIL in .env or RESET_EMAIL=...", file=sys.stderr)
        sys.exit(1)
    new_pw = os.environ.get("NEW_PASSWORD") or "ThreatVisionLocal2026!"
    if len(new_pw) < 8:
        print("Password must be at least 8 characters", file=sys.stderr)
        sys.exit(1)

    pwd_hash = hash_password(new_pw)
    conn = await connect_pg(url, database_ssl=env.get("DATABASE_SSL"))
    try:
        n = await conn.execute(
            "UPDATE users SET password_hash = $2 WHERE lower(email) = lower($1)",
            email,
            pwd_hash,
        )
        if n == "UPDATE 0":
            print(f"No user with email {email!r}", file=sys.stderr)
            sys.exit(1)
    finally:
        await conn.close()

    creds = _BACKEND.parent / ".dev_login_credentials.txt"
    creds.write_text(
        "\n".join(
            [
                "ThreatVision local login",
                "URL:      http://localhost:3001/login",
                f"Email:    {email}",
                f"Password: {new_pw}",
                "",
                "(Reset by: backend/scripts/reset_password.py)",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("Password updated for", email)
    print("Saved:", creds)


if __name__ == "__main__":
    asyncio.run(main())
