"""Lightweight HTTP probes for integrations test-all (M14)."""

from __future__ import annotations

import base64

import httpx

from app.services.ioc.source_catalog import CATALOG_ORDER


def _ibm_basic_header(raw: str) -> str | None:
    parts = raw.split(":", 1)
    if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
        return None
    user, pw = parts[0].strip(), parts[1].strip()
    token = base64.b64encode(f"{user}:{pw}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


async def probe_virustotal(client: httpx.AsyncClient, key: str) -> tuple[bool, str]:
    r = await client.get(
        "https://www.virustotal.com/api/v3/ip_addresses/8.8.8.8",
        headers={"x-apikey": key},
        timeout=25.0,
    )
    if r.status_code in (200, 404):
        return True, "Reachable"
    if r.status_code == 401:
        return False, "Invalid API key (401)"
    return False, f"HTTP {r.status_code}"


async def probe_abuseipdb(client: httpx.AsyncClient, key: str) -> tuple[bool, str]:
    r = await client.get(
        "https://api.abuseipdb.com/api/v2/check",
        params={"ipAddress": "8.8.8.8", "maxAgeInDays": 90},
        headers={"Key": key, "Accept": "application/json"},
        timeout=20.0,
    )
    if r.status_code == 200:
        return True, "Reachable"
    if r.status_code == 401:
        return False, "Invalid API key (401)"
    return False, f"HTTP {r.status_code}"


async def probe_otx_public(client: httpx.AsyncClient) -> tuple[bool, str]:
    r = await client.get(
        "https://otx.alienvault.com/api/v1/indicators/IPv4/8.8.8.8/general",
        timeout=15.0,
    )
    if r.status_code in (200, 404):
        return True, "Reachable (community)"
    return False, f"HTTP {r.status_code}"


async def probe_otx(client: httpx.AsyncClient, key: str) -> tuple[bool, str]:
    r = await client.get(
        "https://otx.alienvault.com/api/v1/user/",
        headers={"X-OTX-API-KEY": key},
        timeout=15.0,
    )
    if r.status_code == 200:
        return True, "Reachable"
    if r.status_code in (401, 403):
        return False, "Invalid or rejected API key"
    return False, f"HTTP {r.status_code}"


async def probe_shodan(client: httpx.AsyncClient, key: str) -> tuple[bool, str]:
    r = await client.get(
        "https://api.shodan.io/account/profile",
        params={"key": key},
        timeout=15.0,
    )
    if r.status_code == 200:
        return True, "Reachable"
    if r.status_code == 401:
        return False, "Invalid API key (401)"
    return False, f"HTTP {r.status_code}"


async def probe_urlscan(client: httpx.AsyncClient, key: str) -> tuple[bool, str]:
    r = await client.get(
        "https://urlscan.io/user/quotas/",
        headers={"API-Key": key},
        timeout=15.0,
    )
    if r.status_code == 200:
        return True, "Reachable"
    if r.status_code in (401, 403):
        return False, "Invalid API key"
    return False, f"HTTP {r.status_code}"


async def probe_greynoise(client: httpx.AsyncClient, key: str) -> tuple[bool, str]:
    r = await client.get(
        "https://api.greynoise.io/v3/community/8.8.8.8",
        headers={"key": key, "Accept": "application/json"},
        timeout=15.0,
    )
    if r.status_code in (200, 404):
        return True, "Reachable"
    if r.status_code == 401:
        return False, "Invalid API key (401)"
    return False, f"HTTP {r.status_code}"


async def probe_ibm_xforce(client: httpx.AsyncClient, raw: str) -> tuple[bool, str]:
    auth = _ibm_basic_header(raw)
    if not auth:
        return False, "Expected api_key:api_password"
    r = await client.get(
        "https://api.xforce.ibm.com/ipr/8.8.8.8",
        headers={"Authorization": auth, "Accept": "application/json"},
        timeout=20.0,
    )
    if r.status_code in (200, 404):
        return True, "Reachable"
    if r.status_code == 401:
        return False, "Invalid credentials (401)"
    return False, f"HTTP {r.status_code}"


async def probe_safebrowsing(client: httpx.AsyncClient, key: str) -> tuple[bool, str]:
    url = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
    params = {"key": key}
    body = {
        "client": {"clientId": "threatvision", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": "http://malware.testing.google.test/testing/malware/"}],
        },
    }
    r = await client.post(url, params=params, json=body, timeout=20.0)
    if r.status_code == 200:
        return True, "Reachable"
    if r.status_code in (400,) and "API key" in (r.text or ""):
        return False, r.text[:200]
    if r.status_code in (401, 403):
        return False, "Invalid API key"
    if r.status_code == 400:
        return True, "Reachable (400 on test URL is acceptable)"
    return False, f"HTTP {r.status_code}"


async def probe_malwarebazaar(client: httpx.AsyncClient) -> tuple[bool, str]:
    r = await client.post(
        "https://mb-api.abuse.ch/api/v1/",
        json={"query": "get_recent", "selector": "time"},
        timeout=20.0,
    )
    if r.status_code == 200:
        try:
            data = r.json()
            if isinstance(data, dict) and data.get("query_status") == "ok":
                return True, "Reachable"
        except ValueError:
            pass
        return True, "HTTP 200"
    return False, f"HTTP {r.status_code}"


async def probe_threatfox(client: httpx.AsyncClient) -> tuple[bool, str]:
    r = await client.get(
        "https://threatfox-api.abuse.ch/api/v1/ping/",
        timeout=15.0,
    )
    if r.status_code == 200:
        return True, "Reachable"
    return False, f"HTTP {r.status_code}"


PROBE_BY_ID: dict[str, object] = {
    "virustotal": probe_virustotal,
    "abuseipdb": probe_abuseipdb,
    "otx": probe_otx,
    "shodan": probe_shodan,
    "urlscan": probe_urlscan,
    "greynoise": probe_greynoise,
    "ibm_xforce": probe_ibm_xforce,
    "safebrowsing": probe_safebrowsing,
}


def display_name(source_id: str) -> str:
    for e in CATALOG_ORDER:
        if e.id == source_id:
            return e.display_name
    return source_id


async def run_probe_for_source(
    client: httpx.AsyncClient,
    source_id: str,
    secrets: dict[str, str],
) -> tuple[str, str, str | None]:
    """
    Returns (status, display_name, detail).
    status in ok | failed | skipped | not_configured
    """
    name = display_name(source_id)
    for e in CATALOG_ORDER:
        if e.id != source_id:
            continue
        if e.id == "misp":
            return "skipped", name, "Use MISP test"
        if not e.requires_api_key:
            if source_id == "malwarebazaar":
                ok, msg = await probe_malwarebazaar(client)
            elif source_id == "threatfox":
                ok, msg = await probe_threatfox(client)
            elif source_id == "otx":
                ok, msg = await probe_otx_public(client)
            else:
                return "skipped", name, "No probe"
            return ("ok" if ok else "failed", name, msg)
        sk = e.secret_key or ""
        key = (secrets.get(sk) or "").strip()
        if not key:
            return "not_configured", name, None
        fn = PROBE_BY_ID.get(source_id)
        if fn is None:
            return "skipped", name, "No HTTP probe for this source"
        ok, msg = await fn(client, key)  # type: ignore[misc]
        return ("ok" if ok else "failed", name, msg)
    return "skipped", source_id, "Unknown source"
