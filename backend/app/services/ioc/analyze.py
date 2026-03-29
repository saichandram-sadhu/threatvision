"""Single-IOC analysis orchestration (M5: MISP + placeholders)."""

from __future__ import annotations

import json
import uuid

import asyncpg

from app.schemas.source_result import AnalyzeResponse, IocPayload, SourceResult
from app.services.ioc.classify import classify_ioc, search_value_for_misp
from app.services.ioc.consensus import aggregate_from_sources
from app.services.ioc.integration_snapshot import load_integration_snapshot
from app.services.ioc.source_catalog import assemble_source_table
from app.services.misp.ioc_search import search_misp_for_value
from app.services.misp.resolve import resolve_misp_for_user


async def analyze_ioc_value(
    pool: asyncpg.Pool,
    *,
    user_id: str,
    raw_ioc: str,
) -> AnalyzeResponse:
    ioc_type, normalized = classify_ioc(raw_ioc)
    search_val = search_value_for_misp(ioc_type, normalized)

    snapshot = await load_integration_snapshot(pool, user_id)

    base_url, api_key, _tag = await resolve_misp_for_user(pool, user_id)
    if base_url and api_key:
        misp_row = await search_misp_for_value(base_url, api_key, search_val)
    else:
        misp_row = SourceResult(
            id="misp",
            displayName="MISP",
            status="not_configured",
            verdict=None,
            detailLines=["Connect your MISP instance in settings or configure a platform fallback."],
            errorCode="not_configured",
        )

    sources = assemble_source_table(ioc_type, snapshot, misp_row)
    aggregate = aggregate_from_sources(sources)

    await _log_activity(pool, user_id, raw_ioc, aggregate.verdict, sources)

    return AnalyzeResponse(
        ioc=IocPayload(raw=raw_ioc, normalized=normalized, type=ioc_type),
        aggregate=aggregate,
        sources=sources,
    )


def _flagged_by(sources: list[SourceResult]) -> list[str]:
    out: list[str] = []
    for s in sources:
        if s.verdict in ("malicious", "suspicious"):
            out.append(s.id)
    return out


async def _log_activity(
    pool: asyncpg.Pool,
    user_id: str,
    raw_ioc: str,
    verdict: str,
    sources: list[SourceResult],
) -> None:
    uid = uuid.UUID(user_id)
    snippet = raw_ioc.strip().replace("\n", " ")[:512]
    flagged = json.dumps(_flagged_by(sources))
    await pool.execute(
        """
        INSERT INTO activity_log (user_id, ioc_snippet, verdict, flagged_by)
        VALUES ($1, $2, $3, $4::jsonb)
        """,
        uid,
        snippet,
        verdict,
        flagged,
    )
