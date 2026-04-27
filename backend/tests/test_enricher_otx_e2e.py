"""OTX enricher end-to-end against mocked HTTP (M18)."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.services.enrichers.context import EnricherContext
from app.services.enrichers.otx import enrich_otx
from app.services.ioc.integration_snapshot import IntegrationSnapshot


@pytest.mark.asyncio
async def test_enrich_otx_ip_malicious_when_pulses(respx_mock: respx.MockRouter) -> None:
    respx_mock.get(
        url__regex=r"https://otx\.alienvault\.com/api/v1/indicators/IPv4/8\.8\.8\.8/general",
    ).mock(return_value=httpx.Response(200, json={"pulse_info": {"count": 7}}))

    snap = IntegrationSnapshot({}, {"otx": "test-key"})
    async with httpx.AsyncClient() as client:
        ctx = EnricherContext(
            ioc_type="ip",
            normalized="8.8.8.8",
            raw_ioc="8.8.8.8",
            snapshot=snap,
            client=client,
        )
        row = await enrich_otx(ctx)

    assert row.id == "otx"
    assert row.status == "ok"
    assert row.verdict == "malicious"
    assert any("Pulses" in line for line in row.detailLines)


@pytest.mark.asyncio
async def test_enrich_otx_domain_404_is_clean(respx_mock: respx.MockRouter) -> None:
    respx_mock.get(
        url__regex=r"https://otx\.alienvault\.com/api/v1/indicators/domain/.+/general",
    ).mock(return_value=httpx.Response(404))

    snap = IntegrationSnapshot({}, {})
    async with httpx.AsyncClient() as client:
        ctx = EnricherContext(
            ioc_type="domain",
            normalized="nonexistent.invalid",
            raw_ioc="nonexistent.invalid",
            snapshot=snap,
            client=client,
        )
        row = await enrich_otx(ctx)

    assert row.verdict == "clean"
    assert "No OTX" in " ".join(row.detailLines)
