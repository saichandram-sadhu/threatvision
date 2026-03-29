"""External enricher runner (respx-mocked HTTP)."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.services.enrichers.context import EnricherContext
from app.services.enrichers.runner import run_enrichers
from app.services.ioc.integration_snapshot import IntegrationSnapshot
from app.services.ioc.source_catalog import assemble_source_table_with_enrichers
from app.schemas.source_result import SourceResult


@pytest.mark.asyncio
async def test_run_enrichers_otx_ip_clean(respx_mock: respx.MockRouter) -> None:
    respx_mock.get(
        url__regex=r"https://otx\.alienvault\.com/api/v1/indicators/IPv4/.+/general",
    ).mock(
        return_value=httpx.Response(200, json={"pulse_info": {"count": 0}}),
    )
    snap = IntegrationSnapshot({}, {})
    async with httpx.AsyncClient() as client:
        ctx = EnricherContext(
            ioc_type="ip",
            normalized="8.8.8.8",
            raw_ioc="8.8.8.8",
            snapshot=snap,
            client=client,
        )
        out = await run_enrichers(ctx)
    assert "otx" in out
    assert out["otx"].status == "ok"
    assert out["otx"].verdict == "clean"


@pytest.mark.asyncio
async def test_run_enrichers_skips_malwarebazaar_when_toggle_off(respx_mock: respx.MockRouter) -> None:
    respx_mock.post("https://mb-api.abuse.ch/api/v1/").mock(
        return_value=httpx.Response(200, json={"query_status": "ok", "data": []}),
    )
    snap = IntegrationSnapshot({"malwarebazaar": False}, {})
    async with httpx.AsyncClient() as client:
        ctx = EnricherContext(
            ioc_type="hash",
            normalized="a" * 64,
            raw_ioc="a" * 64,
            snapshot=snap,
            client=client,
        )
        out = await run_enrichers(ctx)
    assert "malwarebazaar" not in out


def test_assemble_with_enrichers_preserves_order() -> None:
    misp = SourceResult(
        id="misp",
        displayName="MISP",
        status="ok",
        verdict="clean",
        detailLines=[],
    )
    snap = IntegrationSnapshot({}, {})
    enrich = {
        "otx": SourceResult(
            id="otx",
            displayName="AlienVault OTX",
            status="ok",
            verdict="clean",
            detailLines=["x"],
        ),
    }
    rows = assemble_source_table_with_enrichers("ip", snap, misp, enrich)
    assert [r.id for r in rows][:3] == ["misp", "virustotal", "abuseipdb"]
    otx_row = next(r for r in rows if r.id == "otx")
    assert otx_row.verdict == "clean"
