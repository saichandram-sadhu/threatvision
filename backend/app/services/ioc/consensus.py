"""Aggregate verdict from per-source rows (M5: MISP-weighted; M6 extends)."""

from __future__ import annotations

from app.schemas.source_result import AggregateResult, SourceResult


def aggregate_from_sources(sources: list[SourceResult]) -> AggregateResult:
    misp = next((s for s in sources if s.id == "misp"), None)
    if misp is None:
        return AggregateResult(verdict="CLEAN", confidence=10, rationale="No MISP data.")

    if misp.status == "unavailable":
        return AggregateResult(
            verdict="CLEAN",
            confidence=12,
            rationale="MISP could not be queried; confirm connectivity and credentials.",
        )

    if misp.status == "not_configured":
        return AggregateResult(
            verdict="CLEAN",
            confidence=15,
            rationale="MISP is not configured — enable it in settings for authoritative context.",
        )

    if misp.status != "ok" or misp.verdict is None:
        return AggregateResult(verdict="CLEAN", confidence=18, rationale="MISP returned no verdict.")

    if misp.verdict == "malicious":
        return AggregateResult(
            verdict="MALICIOUS",
            confidence=82,
            rationale="MISP contains matching intelligence for this IOC.",
        )
    if misp.verdict == "suspicious":
        return AggregateResult(
            verdict="SUSPICIOUS",
            confidence=58,
            rationale="MISP tagging/TLP suggests elevated but non-definitive risk.",
        )
    return AggregateResult(
        verdict="CLEAN",
        confidence=38,
        rationale="MISP did not surface attribute matches for this value.",
    )
