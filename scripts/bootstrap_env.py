"""
Generate backend/.env and frontend/.env.local for local dev.

SUPERADMIN_EMAIL is copied from ../.env.example if present.

Run (from repo root):
  threatvision\\backend\\.venv\\Scripts\\python.exe threatvision\\scripts\\bootstrap_env.py
"""

from __future__ import annotations

import secrets
from pathlib import Path

from cryptography.fernet import Fernet

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / ".env.example"
BACKEND_ENV = ROOT / "backend" / ".env"
FRONTEND_ENV = ROOT / "frontend" / ".env.local"


def _superadmin_from_example() -> str:
    if EXAMPLE.exists():
        for line in EXAMPLE.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s.startswith("SUPERADMIN_EMAIL=") and not s.startswith("#"):
                return s.split("=", 1)[1].strip()
    return "admin@example.com"


def main() -> None:
    super_email = _superadmin_from_example()
    fernet = Fernet.generate_key().decode("ascii")
    jwt = secrets.token_urlsafe(48)
    bff = secrets.token_urlsafe(48)
    pepper = secrets.token_urlsafe(48)
    nextauth = secrets.token_urlsafe(48)

    db_url = "postgresql://threatvision:threatvision@127.0.0.1:55432/threatvision"
    # 8001: avoids common conflict with other apps on :8000 (e.g. PassFort).
    backend_url = "http://127.0.0.1:8001"

    BACKEND_ENV.write_text(
        "\n".join(
            [
                f"DATABASE_URL={db_url}",
                f"ENCRYPTION_KEY={fernet}",
                f"INTERNAL_JWT_SECRET={jwt}",
                "INTERNAL_JWT_EXPIRE_MINUTES=5",
                f"BFF_SERVICE_KEY={bff}",
                f"API_KEY_PEPPER={pepper}",
                f"SUPERADMIN_EMAIL={super_email}",
                "CORS_ORIGINS=http://localhost:3000",
                "MAX_REQUEST_BODY_BYTES=8388608",
                "DEV_QUICK_ADMIN_LOGIN=true",
                "",
            ]
        ),
        encoding="utf-8",
    )

    FRONTEND_ENV.write_text(
        "\n".join(
            [
                f"NEXTAUTH_SECRET={nextauth}",
                "NEXTAUTH_URL=http://localhost:3000",
                "NEXT_PUBLIC_APP_URL=http://localhost:3000",
                f"BACKEND_URL={backend_url}",
                f"BFF_SERVICE_KEY={bff}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print("Wrote:", BACKEND_ENV)
    print("Wrote:", FRONTEND_ENV)
    print("SUPERADMIN_EMAIL:", super_email)
    print("Register + login with that email to become SUPERADMIN.")


if __name__ == "__main__":
    main()
