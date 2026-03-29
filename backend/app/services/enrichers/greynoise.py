"""GreyNoise Community API (IP only)."""

from __future__ import annotations

import httpx

from app.schemas.source_result import SourceResult
from app.services.enrichers.base import get_json, ok_result, unavailable
from app.services.enrichers.context import EnricherContext


async def enrich_greynoise(ctx: EnricherContext) -> SourceResult:
    if ctx.ioc_type != "ip":
        return SourceResult(
            id="greynoise",
            displayName="GreyNoise Community",
            status="unavailable",
            verdict=None,
            detailLines=["GreyNoise Community applies to IP indicators only."],
            errorCode="unsupported_ioc_type",
        )
    token = (ctx.snapshot.secrets.get("greynoise") or "").strip()
    if not token:
        return SourceResult(
            id="greynoise",
            displayName="GreyNoise Community",
            status="not_configured",
            verdict=None,
            detailLines=["API key not stored in ThreatVision settings."],
            errorCode="missing_api_key",
        )
    url = f"https://api.greynoise.io/v3/community/{ctx.normalized}"
    headers = {"key": token, "Accept": "application/json"}
    try:
        data = await get_json(ctx.client, url, headers=headers, timeout=15.0)
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (404, 400):
            return ok_result(
                "greynoise",
                "GreyNoise Community",
                "clean",
                ["IP not classified as noise/malicious in GreyNoise Community."],
                {},
            )
        return unavailable("greynoise", "GreyNoise Community", "http_error", str(e))
    except Exception as e:  # noqa: BLE001
        return unavailable("greynoise", "GreyNoise Community", "error", str(e))

    classification = str(data.get("classification") or "").lower()
    name = str(data.get("name") or "")[:80]
    riot = data.get("riot")
    lines = [f"Classification: {classification or 'unknown'}"]
    if name:
        lines.append(f"Actor/name: {name}")
    if riot is True:
        return ok_result(
            "greynoise",
            "GreyNoise Community",
            "clean",
            lines + ["Marked as RIOT (common benign service)."],
            {"classification": classification, "riot": True},
        )
    if classification in ("malicious", "malware"):
        return ok_result(
            "greynoise",
            "GreyNoise Community",
            "malicious",
            lines,
            {"classification": classification},
        )
    if classification in ("suspicious", "unknown", "benign"):
        verdict = "suspicious" if classification == "suspicious" else "clean"
        return ok_result(
            "greynoise",
            "GreyNoise Community",
            verdict,
            lines,
            {"classification": classification},
        )
    return ok_result(
        "greynoise",
        "GreyNoise Community",
        "clean",
        lines,
        {"classification": classification},
    )
