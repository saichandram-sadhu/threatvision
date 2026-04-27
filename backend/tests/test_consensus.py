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


def test_consensus_misp_malicious_only() -> None:
    sources = [
        SourceResult(
            id="misp",
            displayName="MISP",
            status="ok",
            verdict="malicious",
            detailLines=["hit"],
        ),
    ]
    agg = aggregate_from_sources(sources)
    assert agg.verdict == "MALICIOUS"
    assert "MISP" in (agg.rationale or "")


def test_consensus_single_misp_suspicious_is_weighted_above_malicious_threshold() -> None:
    """One ``ok`` source with ``suspicious`` still contributes 0.55× weight → ratio > 0.38."""
    sources = [
        SourceResult(
            id="misp",
            displayName="MISP",
            status="ok",
            verdict="suspicious",
            detailLines=[],
        ),
    ]
    agg = aggregate_from_sources(sources)
    assert agg.verdict == "MALICIOUS"


def test_consensus_mid_bucket_suspicious_malicious_vs_cleans() -> None:
    """Weighted ratio in (0.1, 0.38] → SUSPICIOUS (VT malicious vs MISP clean)."""
    sources = [
        SourceResult(
            id="virustotal",
            displayName="VirusTotal",
            status="ok",
            verdict="malicious",
            detailLines=[],
        ),
        SourceResult(
            id="misp",
            displayName="MISP",
            status="ok",
            verdict="clean",
            detailLines=[],
        ),
    ]
    agg = aggregate_from_sources(sources)
    assert agg.verdict == "SUSPICIOUS"


def test_consensus_weighted_clean_majority() -> None:
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
            verdict="clean",
            detailLines=[],
        ),
        SourceResult(
            id="abuseipdb",
            displayName="AbuseIPDB",
            status="ok",
            verdict="clean",
            detailLines=[],
        ),
    ]
    agg = aggregate_from_sources(sources)
    assert agg.verdict == "CLEAN"


def test_consensus_unknown_verdicts_fall_back_to_misp_logic() -> None:
    sources = [
        SourceResult(
            id="misp",
            displayName="MISP",
            status="ok",
            verdict="unknown",
            detailLines=[],
        ),
        SourceResult(
            id="otx",
            displayName="AlienVault OTX",
            status="ok",
            verdict="unknown",
            detailLines=[],
        ),
    ]
    agg = aggregate_from_sources(sources)
    assert agg.verdict == "CLEAN"
