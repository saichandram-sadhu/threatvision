#!/usr/bin/env python3
"""
Local dev: Docker Postgres → migrations → FastAPI (8001) → register SUPERADMIN_EMAIL → Next (3001).
Writes threatvision/.dev_login_credentials.txt (gitignored) with email + password for login.

Run from anywhere:
  d:\\MISP2\\threatvision\\backend\\.venv\\Scripts\\python.exe d:\\MISP2\\threatvision\\scripts\\auto_everything.py
"""

from __future__ import annotations

import json
import os
import secrets
import string
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
ENV_FILE = BACKEND / ".env"
CREDS_FILE = ROOT / ".dev_login_credentials.txt"
VENV_PY = BACKEND / ".venv" / "Scripts" / "python.exe"
if not VENV_PY.is_file():
    VENV_PY = BACKEND / ".venv" / "bin" / "python"
API = "http://127.0.0.1:8001"
WEB = "http://127.0.0.1:3001"


def _load_env_file() -> dict[str, str]:
    out: dict[str, str] = {}
    if not ENV_FILE.is_file():
        print("Missing", ENV_FILE, file=sys.stderr)
        sys.exit(1)
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        out[k.strip()] = v.strip()
    return out


def _http_json(method: str, url: str, body: dict | None = None, timeout: float = 30) -> tuple[int, dict | list | str]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return e.code, raw


def _wait_health(max_wait: float = 90) -> bool:
    deadline = time.time() + max_wait
    while time.time() < deadline:
        code, _ = _http_json("GET", f"{API}/health", None, timeout=3)
        if code == 200:
            return True
        time.sleep(1)
    return False


def _popen_uvicorn() -> subprocess.Popen:
    env = os.environ.copy()
    # Load backend .env into subprocess env
    for k, v in _load_env_file().items():
        env[k] = v
    cmd = [
        str(BACKEND / ".venv" / "Scripts" / "uvicorn.exe"),
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8001",
    ]
    if not cmd[0].startswith(str(BACKEND)):
        cmd[0] = str(BACKEND / ".venv" / "bin" / "uvicorn")
    return subprocess.Popen(
        cmd,
        cwd=str(BACKEND),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )


def _popen_next() -> subprocess.Popen:
    env = os.environ.copy()
    # Next reads frontend/.env.local automatically from cwd
    return subprocess.Popen(
        "npm run dev -- -p 3001",
        cwd=str(FRONTEND),
        env=env,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )


def _port_open(host: str, port: int) -> bool:
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        s.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def main() -> None:
    os.chdir(ROOT)
    env_vars = _load_env_file()
    email = env_vars.get("SUPERADMIN_EMAIL", "admin@example.com").strip().lower()
    name = "ThreatVision Dev"

    print("==> docker compose up -d")
    subprocess.run(["docker", "compose", "up", "-d"], cwd=str(ROOT), check=False)
    time.sleep(7)

    print("==> apply migrations (ok if already applied)")
    r = subprocess.run([str(VENV_PY), str(BACKEND / "scripts" / "apply_migrations.py")], cwd=str(BACKEND))
    if r.returncode != 0:
        print("    (non-zero exit — DB likely already migrated; continuing)")

    if not _port_open("127.0.0.1", 8001):
        print("==> starting FastAPI on 8001")
        _popen_uvicorn()
        if not _wait_health():
            print("API did not become healthy on 8001.", file=sys.stderr)
            sys.exit(1)
    else:
        code, _ = _http_json("GET", f"{API}/health", None, timeout=2)
        if code != 200:
            print("==> starting FastAPI on 8001 (port busy but not our API)")
            _popen_uvicorn()
            if not _wait_health():
                print("API health check failed.", file=sys.stderr)
                sys.exit(1)
        else:
            print("==> API already up on 8001")

    alphabet = string.ascii_letters + string.digits
    password = "".join(secrets.choice(alphabet) for _ in range(20)) + "Aa1"

    print("==> POST /auth/register", email)
    code, body = _http_json(
        "POST",
        f"{API}/auth/register",
        {"email": email, "password": password, "name": name},
    )

    lines = [
        "ThreatVision local login",
        f"URL:      {WEB}/login",
        f"Email:    {email}",
        "",
    ]

    if code == 201 and isinstance(body, dict) and body.get("api_key"):
        lines.append(f"Password: {password}")
        lines.append("")
        lines.append("(API key was returned once; stored only in DB — use password for web login.)")
        print("Registered new user.")
    elif code == 409:
        lines.append("Password: (account already exists — use the password you chose before)")
        lines.append("")
        lines.append("If you forgot it: reset in DB or delete user row and re-run this script.")
        password = "(existing account)"
        print("User already registered — skipped new password.")
    else:
        lines.append(f"Register failed HTTP {code}: {body}")
        CREDS_FILE.write_text("\n".join(lines), encoding="utf-8")
        print("Register failed:", code, body, file=sys.stderr)
        sys.exit(1)

    CREDS_FILE.write_text("\n".join(lines), encoding="utf-8")
    print("Wrote", CREDS_FILE)

    if not _port_open("127.0.0.1", 3001):
        print("==> starting Next.js on 3001")
        _popen_next()
        time.sleep(4)
    else:
        print("==> port 3001 already in use (Next may already run)")

    print("Done. Open:", WEB)
    if code == 201:
        print("Login with email + password from", CREDS_FILE.name)


if __name__ == "__main__":
    main()
