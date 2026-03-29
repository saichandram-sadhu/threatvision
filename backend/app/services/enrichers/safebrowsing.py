"""Google Safe Browsing v4 threatMatches:find."""

from __future__ import annotations

import httpx

from app.schemas.source_result import SourceResult
from app.services.enrichers.base import ok_result, post_json, unavailable
from app.services.enrichers.context import EnricherContext


def _threat_url(ctx: EnricherContext) -> str | None:
    if ctx.ioc_type == "url":
        return ctx.normalized
    if ctx.ioc_type == "domain":
        return f"http://{ctx.normalized}/"
    return None


async def enrich_safebrowsing(ctx: EnricherContext) -> SourceResult:
    check_url = _threat_url(ctx)
    if not check_url:
        return SourceResult(
            id="safebrowsing",
            displayName="Google Safe Browsing",
            status="unavailable",
            verdict=None,
            detailLines=["Safe Browsing applies to URLs and domains only."],
            errorCode="unsupported_ioc_type",
        )
    key = (ctx.snapshot.secrets.get("safebrowsing") or "").strip()
    if not key:
        return SourceResult(
            id="safebrowsing",
            displayName="Google Safe Browsing",
            status="not_configured",
            verdict=None,
            detailLines=["API key not stored in ThreatVision settings."],
            errorCode="missing_api_key",
        )
    api = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
    payload = {
        "client": {"clientId": "threatvision", "clientVersion": "1.0.0"},
        "threatInfo": {
            "threatTypes": [
                "MALWARE",
                "SOCIAL_ENGINEERING",
                "UNWANTED_SOFTWARE",
                "POTENTIALLY_HARMFUL_APPLICATION",
            ],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": check_url}],
        },
    }
    try:
        data = await post_json(
            ctx.client,
            api,
            json_body=payload,
            params={"key": key},
            timeout=15.0,
        )
    except httpx.HTTPStatusError as e:
        return unavailable("safebrowsing", "Google Safe Browsing", "http_error", str(e))
    except Exception as e:  # noqa: BLE001
        return unavailable("safebrowsing", "Google Safe Browsing", "error", str(e))

    matches = data.get("matches")
    if matches:
        kinds = sorted({str(m.get("threatType", "")) for m in matches if isinstance(m, dict)})
        lines = ["Safe Browsing reported a match.", f"Threat types: {', '.join(kinds) or 'unknown'}"]
        return ok_result(
            "safebrowsing",
            "Google Safe Browsing",
            "malicious",
            lines,
            {"match_count": len(matches)},
        )
    return ok_result(
        "safebrowsing",
        "Google Safe Browsing",
        "clean",
        ["No Safe Browsing matches for this URL."],
        {},
    )
