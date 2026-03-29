"""Run applicable external enrichers in parallel."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from app.schemas.source_result import SourceResult
from app.services.enrichers.abuseipdb import enrich_abuseipdb
from app.services.enrichers.base import unavailable
from app.services.enrichers.context import EnricherContext
from app.services.enrichers.greynoise import enrich_greynoise
from app.services.enrichers.ibm_xforce import enrich_ibm_xforce
from app.services.enrichers.malwarebazaar import enrich_malwarebazaar
from app.services.enrichers.otx import enrich_otx
from app.services.enrichers.safebrowsing import enrich_safebrowsing
from app.services.enrichers.shodan import enrich_shodan
from app.services.enrichers.threatfox import enrich_threatfox
from app.services.enrichers.urlscan import enrich_urlscan
from app.services.enrichers.virustotal import enrich_virustotal
from app.services.ioc.integration_snapshot import toggle_enabled
from app.services.ioc.source_catalog import CATALOG_ORDER, CatalogEntry, is_applicable

EnricherFn = Callable[[EnricherContext], Awaitable[SourceResult]]

ENRICHERS: dict[str, EnricherFn] = {
    "virustotal": enrich_virustotal,
    "abuseipdb": enrich_abuseipdb,
    "otx": enrich_otx,
    "shodan": enrich_shodan,
    "urlscan": enrich_urlscan,
    "malwarebazaar": enrich_malwarebazaar,
    "threatfox": enrich_threatfox,
    "safebrowsing": enrich_safebrowsing,
    "greynoise": enrich_greynoise,
    "ibm_xforce": enrich_ibm_xforce,
}


def _display_name(source_id: str) -> str:
    for e in CATALOG_ORDER:
        if e.id == source_id:
            return e.display_name
    return source_id


def _should_run_entry(entry: CatalogEntry, ctx: EnricherContext) -> bool:
    if not is_applicable(entry, ctx.ioc_type):
        return False
    if not toggle_enabled(ctx.snapshot, entry.id, default=True):
        return False
    if entry.requires_api_key:
        sk = entry.secret_key or ""
        if not (ctx.snapshot.secrets.get(sk) or "").strip():
            return False
    return True


async def run_enrichers(ctx: EnricherContext) -> dict[str, SourceResult]:
    tasks: list[tuple[str, Awaitable[SourceResult]]] = []
    for entry in CATALOG_ORDER:
        if entry.id == "misp":
            continue
        fn = ENRICHERS.get(entry.id)
        if fn is None:
            continue
        if not _should_run_entry(entry, ctx):
            continue
        tasks.append((entry.id, fn(ctx)))
    if not tasks:
        return {}
    ids = [t[0] for t in tasks]
    coros = [t[1] for t in tasks]
    raw = await asyncio.gather(*coros, return_exceptions=True)
    out: dict[str, SourceResult] = {}
    for i, res in enumerate(raw):
        sid = ids[i]
        if isinstance(res, BaseException):
            out[sid] = unavailable(sid, _display_name(sid), "error", str(res))
        else:
            out[sid] = res
    return out
