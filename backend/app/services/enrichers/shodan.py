"""Shodan host lookup (IP; domain/URL via DNS resolve)."""

from __future__ import annotations

import httpx

from app.schemas.source_result import SourceResult
from app.services.enrichers.base import get_json, host_from_url, ok_result, unavailable
from app.services.enrichers.context import EnricherContext


async def _shodan_host_json(ctx: EnricherContext, ip: str, key: str) -> dict:
    url = f"https://api.shodan.io/shodan/host/{ip}"
    return await get_json(ctx.client, url, params={"key": key}, timeout=20.0)


async def _resolve_hostname(ctx: EnricherContext, hostname: str, key: str) -> str | None:
    url = "https://api.shodan.io/dns/resolve"
    data = await get_json(
        ctx.client,
        url,
        params={"hostnames": hostname, "key": key},
        timeout=15.0,
    )
    if not isinstance(data, dict):
        return None
    return data.get(hostname) or data.get(hostname.lower())


async def enrich_shodan(ctx: EnricherContext) -> SourceResult:
    key = (ctx.snapshot.secrets.get("shodan") or "").strip()
    if not key:
        return SourceResult(
            id="shodan",
            displayName="Shodan",
            status="not_configured",
            verdict=None,
            detailLines=["API key not stored in ThreatVision settings."],
            errorCode="missing_api_key",
        )

    target_ip: str | None = None
    if ctx.ioc_type == "ip":
        target_ip = ctx.normalized
    elif ctx.ioc_type == "domain":
        try:
            target_ip = await _resolve_hostname(ctx, ctx.normalized, key)
        except Exception:  # noqa: BLE001
            target_ip = None
    elif ctx.ioc_type == "url":
        h = host_from_url(ctx.normalized)
        if h:
            try:
                target_ip = await _resolve_hostname(ctx, h, key)
            except Exception:  # noqa: BLE001
                target_ip = None
    else:
        return SourceResult(
            id="shodan",
            displayName="Shodan",
            status="unavailable",
            verdict=None,
            detailLines=["Shodan applies to IP, domain, and URL indicators only."],
            errorCode="unsupported_ioc_type",
        )

    if not target_ip:
        return ok_result(
            "shodan",
            "Shodan",
            "clean",
            ["Could not resolve host to an IP via Shodan DNS, or host not found."],
            {},
        )

    try:
        data = await _shodan_host_json(ctx, target_ip, key)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return ok_result(
                "shodan",
                "Shodan",
                "clean",
                ["Host IP not indexed in Shodan."],
                {"resolved_ip": target_ip},
            )
        return unavailable("shodan", "Shodan", "http_error", str(e))
    except Exception as e:  # noqa: BLE001
        return unavailable("shodan", "Shodan", "error", str(e))

    vulns = data.get("vulns") or []
    if isinstance(vulns, dict):
        vuln_count = len(vulns)
    else:
        vuln_count = len(vulns) if isinstance(vulns, list) else 0
    org = (data.get("org") or "")[:120]
    ports = data.get("ports") or []
    port_preview = ports[:8]
    lines = [
        f"Resolved IP: {target_ip}",
        f"Open ports (sample): {port_preview}" if port_preview else "Open ports: none listed",
    ]
    if org:
        lines.append(f"Org: {org}")
    if vuln_count:
        lines.append(f"Known CVEs tagged: {vuln_count}")
        verdict = "malicious" if vuln_count >= 3 else "suspicious"
    else:
        verdict = "clean"
    return ok_result(
        "shodan",
        "Shodan",
        verdict,
        lines,
        {"vuln_count": vuln_count, "resolved_ip": target_ip},
    )
