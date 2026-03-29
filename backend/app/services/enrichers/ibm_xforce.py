"""IBM X-Force Exchange (Basic auth; secret format ``key:password``)."""

from __future__ import annotations

import base64

import httpx

from app.schemas.source_result import SourceResult
from app.services.enrichers.base import get_json, ok_result, quote_path, unavailable
from app.services.enrichers.context import EnricherContext


def _basic_header(raw: str) -> str | None:
    parts = raw.split(":", 1)
    if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
        return None
    user, pw = parts[0].strip(), parts[1].strip()
    token = base64.b64encode(f"{user}:{pw}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


async def enrich_ibm_xforce(ctx: EnricherContext) -> SourceResult:
    secret = (ctx.snapshot.secrets.get("ibm_xforce") or "").strip()
    if not secret:
        return SourceResult(
            id="ibm_xforce",
            displayName="IBM X-Force",
            status="not_configured",
            verdict=None,
            detailLines=["Credentials not stored (expected ``api_key:api_password``)."],
            errorCode="missing_api_key",
        )
    auth = _basic_header(secret)
    if not auth:
        return SourceResult(
            id="ibm_xforce",
            displayName="IBM X-Force",
            status="not_configured",
            verdict=None,
            detailLines=["ibm_xforce secret must be ``key:password``."],
            errorCode="invalid_credentials_format",
        )
    headers = {"Authorization": auth, "Accept": "application/json"}
    t = ctx.ioc_type
    val = ctx.normalized
    base = "https://api.xforce.ibmcloud.com"
    try:
        if t == "ip":
            path = f"/ipr/{quote_path(val)}"
            data = await get_json(ctx.client, f"{base}{path}", headers=headers, timeout=20.0)
            score = data.get("score")
            cats = data.get("cats") or {}
            if isinstance(cats, dict) and cats:
                top = max(cats.items(), key=lambda x: float(x[1] or 0))
                lines = [f"Risk score: {score}", f"Top category: {top[0]} ({top[1]})"]
            else:
                lines = [f"Risk score: {score}"]
            try:
                sc = float(score)
            except (TypeError, ValueError):
                sc = 0.0
            if sc >= 5.0:
                verdict = "malicious"
            elif sc >= 2.0:
                verdict = "suspicious"
            else:
                verdict = "clean"
            return ok_result("ibm_xforce", "IBM X-Force", verdict, lines, {"score": score})

        if t == "domain":
            path = f"/resolve/{quote_path(val)}"
            data = await get_json(ctx.client, f"{base}{path}", headers=headers, timeout=20.0)
            rec = (data.get("records") or [])
            if isinstance(rec, list) and rec:
                lines = [f"Passive DNS / resolve records: {len(rec)}"]
                return ok_result("ibm_xforce", "IBM X-Force", "suspicious", lines, {"record_count": len(rec)})
            return ok_result(
                "ibm_xforce",
                "IBM X-Force",
                "clean",
                ["No notable X-Force records for this domain."],
                {},
            )

        if t == "hash":
            path = f"/malware/{quote_path(val.lower())}"
            data = await get_json(ctx.client, f"{base}{path}", headers=headers, timeout=20.0)
            mal = data.get("malware") or {}
            family = str(mal.get("family") or data.get("family") or "malware")[:120]
            lines = [f"X-Force malware corpus: {family}"]
            return ok_result("ibm_xforce", "IBM X-Force", "malicious", lines, {})

        return SourceResult(
            id="ibm_xforce",
            displayName="IBM X-Force",
            status="unavailable",
            verdict=None,
            detailLines=["IBM X-Force enricher supports IP, domain, and hash only."],
            errorCode="unsupported_ioc_type",
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return ok_result(
                "ibm_xforce",
                "IBM X-Force",
                "clean",
                ["No X-Force record for this IOC."],
                {},
            )
        return unavailable("ibm_xforce", "IBM X-Force", "http_error", str(e))
    except Exception as e:  # noqa: BLE001
        return unavailable("ibm_xforce", "IBM X-Force", "error", str(e))
