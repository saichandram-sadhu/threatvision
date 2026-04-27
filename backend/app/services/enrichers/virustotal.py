"""VirusTotal v3 REST."""

from __future__ import annotations

import httpx

from app.schemas.source_result import SourceResult
from app.services.enrichers.base import get_json, not_configured_row, ok_result, quote_path, unavailable, vt_url_identifier
from app.services.enrichers.context import EnricherContext


async def enrich_virustotal(ctx: EnricherContext) -> SourceResult:
    key = (ctx.snapshot.secrets.get("virustotal") or "").strip()
    if not key:
        return not_configured_row("virustotal", "VirusTotal")
    headers = {"x-apikey": key}
    t = ctx.ioc_type
    val = ctx.normalized
    if t == "ip":
        path = f"ip_addresses/{quote_path(val)}"
    elif t == "domain":
        path = f"domains/{quote_path(val)}"
    elif t == "url":
        path = f"urls/{vt_url_identifier(val)}"
    elif t == "hash":
        path = f"files/{quote_path(val.lower())}"
    else:
        path = f"domains/{quote_path(val[:200])}"

    url = f"https://www.virustotal.com/api/v3/{path}"
    try:
        data = await get_json(ctx.client, url, headers=headers, timeout=25.0)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return ok_result(
                "virustotal",
                "VirusTotal",
                "clean",
                ["IOC not present in VirusTotal corpus."],
                {},
            )
        if e.response.status_code == 401:
            return unavailable(
                "virustotal",
                "VirusTotal",
                "invalid_api_key",
                "VirusTotal returned 401 — the API key is invalid or revoked. "
                "Copy your private API key from virusTotal.com (API key page), paste it in Integrations with no spaces, and save.",
            )
        if e.response.status_code == 429:
            return unavailable("virustotal", "VirusTotal", "http_429", "VirusTotal rate limit (429).")
        return unavailable("virustotal", "VirusTotal", "http_error", str(e))
    except Exception as e:  # noqa: BLE001
        return unavailable("virustotal", "VirusTotal", "error", str(e))

    attrs = (data.get("data") or {}).get("attributes") or {}
    stats = attrs.get("last_analysis_stats") or {}
    mal = int(stats.get("malicious", 0) or 0)
    sus = int(stats.get("suspicious", 0) or 0)
    harm = int(stats.get("harmless", 0) or 0)
    und = int(stats.get("undetected", 0) or 0)
    total = mal + sus + harm + und
    lines = [
        f"Malicious: {mal}",
        f"Suspicious: {sus}",
        f"Harmless: {harm}",
        f"Undetected: {und}",
    ]
    if mal >= 4 or (mal >= 1 and mal > sus + harm):
        verdict = "malicious"
    elif mal + sus >= 1:
        verdict = "suspicious"
    else:
        verdict = "clean"
    return ok_result(
        "virustotal",
        "VirusTotal",
        verdict,
        lines + ([f"Engines: {total}"] if total else []),
        {"last_analysis_stats": stats},
    )
