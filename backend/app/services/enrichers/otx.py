"""AlienVault OTX (optional API key)."""

from __future__ import annotations

import httpx

from app.services.enrichers.base import get_json, host_from_url, ok_result, quote_path, unavailable
from app.services.enrichers.context import EnricherContext
from app.schemas.source_result import SourceResult


async def enrich_otx(ctx: EnricherContext) -> SourceResult:
    key = (ctx.snapshot.secrets.get("otx") or "").strip()
    headers: dict[str, str] = {}
    if key:
        headers["X-OTX-API-KEY"] = key

    t = ctx.ioc_type
    val = ctx.normalized
    if t == "ip":
        segment, path_val = "IPv4", val
    elif t == "domain":
        segment, path_val = "domain", val
    elif t == "hash":
        segment, path_val = "file", val.lower()
    elif t == "url":
        h = host_from_url(val) or val
        segment, path_val = "hostname", h
    else:
        segment, path_val = "domain", val[:200]

    url = f"https://otx.alienvault.com/api/v1/indicators/{segment}/{quote_path(path_val)}/general"
    try:
        data = await get_json(ctx.client, url, headers=headers, timeout=20.0)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return ok_result(
                "otx",
                "AlienVault OTX",
                "clean",
                ["No OTX community data for this indicator."],
                {"pulse_count": 0},
            )
        return unavailable("otx", "AlienVault OTX", "http_error", str(e))
    except Exception as e:  # noqa: BLE001
        return unavailable("otx", "AlienVault OTX", "error", str(e))

    pulse = (data.get("pulse_info") or {}).get("count", 0) or 0
    if pulse:
        return ok_result(
            "otx",
            "AlienVault OTX",
            "malicious",
            [f"Pulses: {pulse}"],
            {"pulse_count": pulse},
        )
    return ok_result(
        "otx",
        "AlienVault OTX",
        "clean",
        ["No OTX pulses linked to this indicator."],
        {"pulse_count": 0},
    )
