"""Ordered vendor catalog + applicability (spec §4.4)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet

from app.schemas.source_result import SourceResult
from app.services.ioc.classify import IocType
from app.services.ioc.integration_snapshot import IntegrationSnapshot, toggle_enabled


@dataclass(frozen=True)
class CatalogEntry:
    id: str
    display_name: str
    requires_api_key: bool
    secret_key: str | None  # key inside decrypted secrets JSON
    applicable_types: FrozenSet[str] | None  # None = all types


_ALL: FrozenSet[str] | None = None

CATALOG_ORDER: list[CatalogEntry] = [
    CatalogEntry("misp", "MISP", False, None, _ALL),
    CatalogEntry("virustotal", "VirusTotal", True, "virustotal", _ALL),
    CatalogEntry("abuseipdb", "AbuseIPDB", True, "abuseipdb", frozenset({"ip"})),
    CatalogEntry("otx", "AlienVault OTX", False, None, frozenset({"ip", "hash", "domain", "url", "email_header"})),
    CatalogEntry("shodan", "Shodan", True, "shodan", frozenset({"ip", "domain", "url"})),
    CatalogEntry("urlscan", "URLScan.io", True, "urlscan", frozenset({"url", "domain"})),
    CatalogEntry("malwarebazaar", "MalwareBazaar", False, None, frozenset({"hash"})),
    CatalogEntry("threatfox", "ThreatFox", False, None, frozenset({"ip", "hash", "domain"})),
    CatalogEntry("safebrowsing", "Google Safe Browsing", True, "safebrowsing", frozenset({"url", "domain"})),
    CatalogEntry("greynoise", "GreyNoise Community", True, "greynoise", frozenset({"ip"})),
    CatalogEntry("ibm_xforce", "IBM X-Force", True, "ibm_xforce", frozenset({"ip", "domain", "hash"})),
]


def is_applicable(entry: CatalogEntry, ioc_type: IocType) -> bool:
    if entry.applicable_types is None:
        return True
    return ioc_type in entry.applicable_types


def build_non_misp_placeholder(
    entry: CatalogEntry,
    ioc_type: IocType,
    snapshot: IntegrationSnapshot,
) -> SourceResult:
    if not is_applicable(entry, ioc_type):
        return SourceResult(
            id=entry.id,
            displayName=entry.display_name,
            status="ok",
            verdict="unknown",
            detailLines=["Not applicable for this IOC type"],
        )

    if entry.requires_api_key:
        sk = entry.secret_key or ""
        key_val = (snapshot.secrets.get(sk) or "").strip()
        if sk not in snapshot.secrets or not key_val:
            return SourceResult(
                id=entry.id,
                displayName=entry.display_name,
                status="not_configured",
                verdict=None,
                detailLines=["API key not stored in ThreatVision settings."],
                errorCode="missing_api_key",
            )
        return SourceResult(
            id=entry.id,
            displayName=entry.display_name,
            status="not_configured",
            verdict=None,
            detailLines=["Enricher integration scheduled for a later release (M6)."],
            errorCode="pending_integration",
        )

    if not toggle_enabled(snapshot, entry.id, default=True):
        return SourceResult(
            id=entry.id,
            displayName=entry.display_name,
            status="not_configured",
            verdict=None,
            detailLines=["Source disabled in settings."],
            errorCode="disabled",
        )
    return SourceResult(
        id=entry.id,
        displayName=entry.display_name,
        status="not_configured",
        verdict=None,
        detailLines=["Enricher integration scheduled for a later release (M6)."],
        errorCode="pending_integration",
    )


def assemble_source_table(
    ioc_type: IocType,
    snapshot: IntegrationSnapshot,
    misp_row: SourceResult,
) -> list[SourceResult]:
    out: list[SourceResult] = []
    for entry in CATALOG_ORDER:
        if entry.id == "misp":
            out.append(misp_row)
        else:
            out.append(build_non_misp_placeholder(entry, ioc_type, snapshot))
    return out


def assemble_source_table_with_enrichers(
    ioc_type: IocType,
    snapshot: IntegrationSnapshot,
    misp_row: SourceResult,
    enricher_results: dict[str, SourceResult],
) -> list[SourceResult]:
    """Merge live enricher rows into the catalog order; missing ids use placeholders."""
    out: list[SourceResult] = []
    for entry in CATALOG_ORDER:
        if entry.id == "misp":
            out.append(misp_row)
        elif entry.id in enricher_results:
            out.append(enricher_results[entry.id])
        else:
            out.append(build_non_misp_placeholder(entry, ioc_type, snapshot))
    return out
