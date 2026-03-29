"""Shared helpers for enricher modules."""

from __future__ import annotations

import base64
from typing import Any
from urllib.parse import quote, urlparse

import httpx

from app.schemas.source_result import SourceResult, SourceVerdict


def vt_url_identifier(url: str) -> str:
    """VirusTotal v3 URL id (url-safe base64 without padding)."""
    b = base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii")
    return b.rstrip("=")


def host_from_url(normalized_url: str) -> str | None:
    try:
        p = urlparse(normalized_url)
        return p.hostname
    except Exception:  # noqa: BLE001
        return None


async def get_json(client: httpx.AsyncClient, url: str, **kwargs: Any) -> Any:
    r = await client.get(url, **kwargs)
    r.raise_for_status()
    return r.json()


async def post_json(
    client: httpx.AsyncClient,
    url: str,
    json_body: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    **kwargs: Any,
) -> Any:
    r = await client.post(url, json=json_body, data=data, **kwargs)
    r.raise_for_status()
    return r.json()


def ok_result(
    sid: str,
    display: str,
    verdict: SourceVerdict,
    lines: list[str],
    metadata: dict[str, Any] | None = None,
) -> SourceResult:
    return SourceResult(
        id=sid,
        displayName=display,
        status="ok",
        verdict=verdict,
        detailLines=lines[:8],
        metadata=metadata or {},
    )


def unavailable(sid: str, display: str, code: str, message: str) -> SourceResult:
    return SourceResult(
        id=sid,
        displayName=display,
        status="unavailable",
        verdict=None,
        detailLines=[message[:500]],
        errorCode=code,
    )


def not_configured_row(sid: str, display: str) -> SourceResult:
    return SourceResult(
        id=sid,
        displayName=display,
        status="not_configured",
        verdict=None,
        detailLines=["API key not stored in ThreatVision settings."],
        errorCode="missing_api_key",
    )


def quote_path(s: str) -> str:
    return quote(s, safe="")
