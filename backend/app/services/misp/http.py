"""Low-level async JSON calls to MISP (Authorization: API key)."""

from __future__ import annotations

from typing import Any

import httpx

MISP_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}


def _auth_headers(api_key: str) -> dict[str, str]:
    return {**MISP_HEADERS, "Authorization": api_key}


async def misp_get_json(
    base_url: str,
    api_key: str,
    path: str,
    *,
    timeout: float = 30.0,
) -> Any:
    """GET ``path`` (e.g. ``/servers/getVersion.json``) relative to ``base_url``."""
    root = base_url.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    url = f"{root}{path}"
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout), follow_redirects=True) as client:
        r = await client.get(url, headers=_auth_headers(api_key))
        r.raise_for_status()
        return r.json()


async def misp_post_json(
    base_url: str,
    api_key: str,
    path: str,
    body: dict[str, Any],
    *,
    timeout: float = 45.0,
) -> Any:
    root = base_url.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    url = f"{root}{path}"
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout), follow_redirects=True) as client:
        r = await client.post(url, headers=_auth_headers(api_key), json=body)
        r.raise_for_status()
        return r.json()


async def misp_ping_version(base_url: str, api_key: str) -> dict[str, Any]:
    """Return MISP version payload; tries common REST paths."""
    last_err: Exception | None = None
    for path in ("/servers/getVersion.json", "/servers/getVersion"):
        try:
            data = await misp_get_json(base_url, api_key, path)
            if isinstance(data, dict):
                return data
        except Exception as e:  # noqa: BLE001 — aggregate paths
            last_err = e
            continue
    if last_err:
        raise last_err
    raise RuntimeError("Empty MISP version response")
