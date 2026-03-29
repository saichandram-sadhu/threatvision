"""urlscan.io search (domain / URL host)."""

from __future__ import annotations

import httpx

from app.schemas.source_result import SourceResult
from app.services.enrichers.base import get_json, host_from_url, ok_result, unavailable
from app.services.enrichers.context import EnricherContext


def _query_host(ctx: EnricherContext) -> str | None:
    if ctx.ioc_type == "domain":
        return ctx.normalized
    if ctx.ioc_type == "url":
        return host_from_url(ctx.normalized)
    return None


async def enrich_urlscan(ctx: EnricherContext) -> SourceResult:
    host = _query_host(ctx)
    if not host:
        return SourceResult(
            id="urlscan",
            displayName="urlscan.io",
            status="unavailable",
            verdict=None,
            detailLines=["urlscan.io search is enabled for domains and URLs only."],
            errorCode="unsupported_ioc_type",
        )
    key = (ctx.snapshot.secrets.get("urlscan") or "").strip()
    if not key:
        return SourceResult(
            id="urlscan",
            displayName="urlscan.io",
            status="not_configured",
            verdict=None,
            detailLines=["API key not stored in ThreatVision settings."],
            errorCode="missing_api_key",
        )
    url = "https://urlscan.io/api/v1/search/"
    params = {"q": f'page.domain:"{host}"', "size": 5}
    headers = {"API-Key": key, "Accept": "application/json"}
    try:
        data = await get_json(ctx.client, url, params=params, headers=headers, timeout=20.0)
    except httpx.HTTPStatusError as e:
        return unavailable("urlscan", "urlscan.io", "http_error", str(e))
    except Exception as e:  # noqa: BLE001
        return unavailable("urlscan", "urlscan.io", "error", str(e))

    total = int(data.get("total") or 0)
    results = data.get("results") or []
    malicious_hits = 0
    for item in results[:5]:
        page = (item or {}).get("page") or {}
        if str(page.get("malicious", "")).lower() == "true" or page.get("malicious") is True:
            malicious_hits += 1
    lines = [f"Total scans matching host: {total}"]
    if malicious_hits:
        lines.append(f"Flagged malicious in sample: {malicious_hits}")
    if malicious_hits >= 1:
        verdict = "malicious"
    elif total >= 3:
        verdict = "suspicious"
    else:
        verdict = "clean"
    return ok_result(
        "urlscan",
        "urlscan.io",
        verdict,
        lines,
        {"total": total, "malicious_hits": malicious_hits},
    )
