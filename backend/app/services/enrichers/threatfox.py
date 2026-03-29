"""ThreatFox (abuse.ch) — no API key."""

from __future__ import annotations

import httpx

from app.schemas.source_result import SourceResult
from app.services.enrichers.base import host_from_url, ok_result, post_json, unavailable
from app.services.enrichers.context import EnricherContext


def _tf_hash_type(h: str) -> str:
    n = len(h)
    if n == 32:
        return "hash:md5"
    if n == 40:
        return "hash:sha1"
    if n == 64:
        return "hash:sha256"
    return "hash:sha256"


async def enrich_threatfox(ctx: EnricherContext) -> SourceResult:
    t = ctx.ioc_type
    val = ctx.normalized
    if t == "ip":
        body = {"query": "search_ioc", "ioc_type": "ip:port", "ioc": f"{val}:443"}
    elif t == "domain":
        body = {"query": "search_ioc", "ioc_type": "domain", "ioc": val}
    elif t == "hash":
        body = {"query": "search_ioc", "ioc_type": _tf_hash_type(val), "ioc": val.lower()}
    elif t == "url":
        host = host_from_url(val)
        if not host:
            return SourceResult(
                id="threatfox",
                displayName="ThreatFox",
                status="unavailable",
                verdict=None,
                detailLines=["Could not derive host from URL for ThreatFox lookup."],
                errorCode="unsupported_ioc_type",
            )
        body = {"query": "search_ioc", "ioc_type": "domain", "ioc": host}
    else:
        return SourceResult(
            id="threatfox",
            displayName="ThreatFox",
            status="unavailable",
            verdict=None,
            detailLines=["ThreatFox does not cover this IOC type."],
            errorCode="unsupported_ioc_type",
        )

    url = "https://threatfox-api.abuse.ch/api/v1/"
    try:
        data = await post_json(ctx.client, url, json_body=body, timeout=20.0)
    except httpx.HTTPStatusError as e:
        return unavailable("threatfox", "ThreatFox", "http_error", str(e))
    except Exception as e:  # noqa: BLE001
        return unavailable("threatfox", "ThreatFox", "error", str(e))

    status = str(data.get("query_status") or "")
    if status != "ok":
        return ok_result(
            "threatfox",
            "ThreatFox",
            "clean",
            [f"ThreatFox: {data.get('error_message') or status}"],
            {},
        )
    iocs = data.get("data") or []
    cnt = len(iocs) if isinstance(iocs, list) else 0
    if cnt == 0:
        return ok_result(
            "threatfox",
            "ThreatFox",
            "clean",
            ["No ThreatFox IOCs matched this value."],
            {"match_count": 0},
        )
    lines = [f"ThreatFox IOC matches: {cnt}"]
    return ok_result(
        "threatfox",
        "ThreatFox",
        "malicious",
        lines,
        {"match_count": cnt},
    )
