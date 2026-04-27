"""Issue a key via Cake and validate it both in Cake and over HTTP (no key printed)."""

from __future__ import annotations

import subprocess
import sys

import httpx


def _issue_key() -> str:
    cmd = [
        "docker",
        "exec",
        "misp-misp-core-1",
        "bash",
        "-lc",
        "cd /var/www/MISP/app && ./Console/cake user change_authkey admin@admin.test",
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    txt = (out.stdout or "") + "\n" + (out.stderr or "")
    marker = "Authentication key changed to:"
    if marker not in txt:
        print(txt[:600], file=sys.stderr)
        raise RuntimeError("Cannot parse key output")
    key = txt.split(marker, 1)[1].strip().splitlines()[0].strip()
    return key


def _cake_valid(key: str) -> bool:
    cmd = [
        "docker",
        "exec",
        "-i",
        "misp-misp-core-1",
        "bash",
        "-lc",
        "cd /var/www/MISP/app && ./Console/cake user authkey_valid",
    ]
    out = subprocess.run(cmd, input=key, capture_output=True, text=True, timeout=60)
    txt = (out.stdout or "") + "\n" + (out.stderr or "")
    return "Authkey is valid" in txt or out.returncode == 0


def _http_valid(key: str) -> tuple[int, str]:
    r = httpx.get(
        "https://127.0.0.1/feeds/index.json",
        headers={"Authorization": key, "Accept": "application/json"},
        verify=False,
        timeout=30.0,
        follow_redirects=True,
    )
    return r.status_code, (r.text or "")[:180].replace("\n", " ")


def main() -> int:
    key = _issue_key()
    c_valid = _cake_valid(key)
    status, snippet = _http_valid(key)
    print(f"cake_valid={c_valid} http_status={status} body_snippet={snippet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
