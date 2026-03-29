"""Aggregate verdict from per-source rows (M6: weighted multi-source + MISP)."""

from __future__ import annotations

from app.schemas.source_result import AggregateResult, SourceResult

# Higher weight = more influence when status is ``ok`` and verdict is set.
SOURCE_WEIGHTS: dict[str, float] = {
    "misp": 40.0,
    "virustotal": 22.0,
    "abuseipdb": 10.0,
    "otx": 12.0,
    "shodan": 8.0,
    "urlscan": 8.0,
    "malwarebazaar": 14.0,
    "threatfox": 12.0,
    "safebrowsing": 14.0,
    "greynoise": 8.0,
    "ibm_xforce": 10.0,
}


def _misp_only_aggregate(sources: list[SourceResult]) -> AggregateResult:
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


def aggregate_from_sources(sources: list[SourceResult]) -> AggregateResult:
    """Blend ``ok`` source verdicts with weights; fall back to MISP-only if none qualify."""
    scored = [
        s
        for s in sources
        if s.status == "ok" and s.verdict is not None and s.verdict != "unknown"
    ]
    if not scored:
        return _misp_only_aggregate(sources)

    total_w = 0.0
    score = 0.0
    contributions: list[tuple[str, float]] = []

    for s in scored:
        w = SOURCE_WEIGHTS.get(s.id, 6.0)
        total_w += w
        delta = 0.0
        if s.verdict == "malicious":
            delta = w
        elif s.verdict == "suspicious":
            delta = 0.55 * w
        elif s.verdict == "clean":
            delta = -0.32 * w
        score += delta
        if delta != 0:
            contributions.append((s.displayName, delta))

    if total_w <= 0:
        return _misp_only_aggregate(sources)

    ratio = score / total_w
    if ratio > 0.38:
        return AggregateResult(
            verdict="MALICIOUS",
            confidence=min(96, max(62, int(55 + 40 * min(1.0, ratio)))),
            rationale=_rationale_from_contributions(contributions, "MALICIOUS"),
        )
    if ratio > 0.1:
        return AggregateResult(
            verdict="SUSPICIOUS",
            confidence=min(88, max(42, int(38 + 45 * min(1.0, (ratio - 0.1) / 0.28)))),
            rationale=_rationale_from_contributions(contributions, "SUSPICIOUS"),
        )
    return AggregateResult(
        verdict="CLEAN",
        confidence=min(72, max(22, int(28 + 44 * max(0.0, 1.0 + ratio)))),
        rationale=_rationale_from_contributions(contributions, "CLEAN"),
    )


def _rationale_from_contributions(
    contributions: list[tuple[str, float]],
    bucket: str,
) -> str:
    if not contributions:
        return f"Weighted consensus ({bucket}) from configured sources."
    top = sorted(contributions, key=lambda x: abs(x[1]), reverse=True)[:4]
    parts = [f"{name} ({delta:+.1f})" for name, delta in top]
    return f"Weighted blend ({bucket}): " + "; ".join(parts)
