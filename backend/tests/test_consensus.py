"""Weighted aggregate verdict."""

from __future__ import annotations

from app.schemas.source_result import SourceResult
from app.services.ioc.consensus import aggregate_from_sources


def test_consensus_misp_only_when_no_scored_sources() -> None:
    misp = SourceResult(
        id="misp",
        displayName="MISP",
        status="not_configured",
        verdict=None,
        detailLines=[],
    )
    agg = aggregate_from_sources([misp])
    assert agg.verdict == "CLEAN"
    assert "MISP" in (agg.rationale or "")


def test_consensus_weighted_malicious_from_enrichers() -> None:
    sources = [
        SourceResult(
            id="misp",
            displayName="MISP",
            status="ok",
            verdict="clean",
            detailLines=[],
        ),
        SourceResult(
            id="virustotal",
            displayName="VirusTotal",
            status="ok",
            verdict="malicious",
            detailLines=[],
        ),
        SourceResult(
            id="safebrowsing",
            displayName="Google Safe Browsing",
            status="ok",
            verdict="malicious",
            detailLines=[],
        ),
        SourceResult(
            id="threatfox",
            displayName="ThreatFox",
            status="ok",
            verdict="malicious",
            detailLines=[],
        ),
    ]
    agg = aggregate_from_sources(sources)
    assert agg.verdict == "MALICIOUS"
    assert agg.confidence >= 60
