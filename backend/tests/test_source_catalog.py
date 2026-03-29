"""Vendor grid placeholders."""

from __future__ import annotations

from app.schemas.source_result import SourceResult
from app.services.ioc.integration_snapshot import IntegrationSnapshot
from app.services.ioc.source_catalog import assemble_source_table


def test_assemble_ip_row_abuseipdb_not_configured() -> None:
    snap = IntegrationSnapshot({}, {})
    misp = SourceResult(
        id="misp",
        displayName="MISP",
        status="not_configured",
        verdict=None,
        detailLines=[],
    )
    rows = assemble_source_table("ip", snap, misp)
    assert len(rows) == 11
    assert rows[0].id == "misp"
    abuse = next(r for r in rows if r.id == "abuseipdb")
    assert abuse.status == "not_configured"
    vt = next(r for r in rows if r.id == "urlscan")
    assert vt.detailLines[0] == "Not applicable for this IOC type"
