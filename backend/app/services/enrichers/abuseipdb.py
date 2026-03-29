"""AbuseIPDB v2 (IP only)."""

from __future__ import annotations

import httpx

from app.schemas.source_result import SourceResult
from app.services.enrichers.base import get_json, ok_result, unavailable
from app.services.enrichers.context import EnricherContext


async def enrich_abuseipdb(ctx: EnricherContext) -> SourceResult:
    if ctx.ioc_type != "ip":
        return SourceResult(
            id="abuseipdb",
            displayName="AbuseIPDB",
            status="unavailable",
            verdict=None,
            detailLines=["AbuseIPDB applies to IPv4/IPv6 indicators only."],
            errorCode="unsupported_ioc_type",
        )
    key = (ctx.snapshot.secrets.get("abuseipdb") or "").strip()
    if not key:
        return SourceResult(
            id="abuseipdb",
            displayName="AbuseIPDB",
            status="not_configured",
            verdict=None,
            detailLines=["API key not stored in ThreatVision settings."],
            errorCode="missing_api_key",
        )
    url = "https://api.abuseipdb.com/api/v2/check"
    params = {"ipAddress": ctx.normalized, "maxAgeInDays": 90}
    headers = {"Key": key, "Accept": "application/json"}
    try:
        data = await get_json(ctx.client, url, params=params, headers=headers, timeout=15.0)
    except httpx.HTTPStatusError as e:
        return unavailable("abuseipdb", "AbuseIPDB", "http_error", str(e))
    except Exception as e:  # noqa: BLE001
        return unavailable("abuseipdb", "AbuseIPDB", "error", str(e))

    rec = (data.get("data") or {})
    score = int(rec.get("abuseConfidenceScore") or 0)
    reports = int(rec.get("totalReports") or 0)
    lines = [f"Abuse confidence: {score}%", f"Reports (window): {reports}"]
    if score >= 50 or reports >= 10:
        verdict = "malicious"
    elif score >= 15 or reports >= 1:
        verdict = "suspicious"
    else:
        verdict = "clean"
    return ok_result(
        "abuseipdb",
        "AbuseIPDB",
        verdict,
        lines,
        {"abuseConfidenceScore": score, "totalReports": reports},
    )
