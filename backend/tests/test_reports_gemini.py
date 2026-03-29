"""Gemini executive summary (mocked HTTP)."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.schemas.source_result import AggregateResult, AnalyzeResponse, IocPayload, SourceResult
from app.services.reports.gemini import PLACEHOLDER_FAILURE, summarize_analyses


def _sample_analysis() -> AnalyzeResponse:
    return AnalyzeResponse(
        ioc=IocPayload(raw="8.8.8.8", normalized="8.8.8.8", type="ip"),
        aggregate=AggregateResult(verdict="CLEAN", confidence=40, rationale="Weighted blend"),
        sources=[
            SourceResult(
                id="misp",
                displayName="MISP",
                status="ok",
                verdict="clean",
                detailLines=["No hits"],
            ),
        ],
    )


@pytest.mark.asyncio
async def test_summarize_without_api_key_returns_placeholder() -> None:
    text = await summarize_analyses(None, [_sample_analysis()])
    assert "GEMINI" in text or "not configured" in text.lower()


@pytest.mark.asyncio
async def test_summarize_http_error_returns_placeholder(respx_mock: respx.MockRouter) -> None:
    respx_mock.post(url__regex=r"https://generativelanguage\.googleapis\.com/.*").mock(
        return_value=httpx.Response(500, json={}),
    )
    out = await summarize_analyses("fake-key", [_sample_analysis()])
    assert out == PLACEHOLDER_FAILURE


@pytest.mark.asyncio
async def test_summarize_success_parses_candidate_text(respx_mock: respx.MockRouter) -> None:
    respx_mock.post(url__regex=r"https://generativelanguage\.googleapis\.com/.*").mock(
        return_value=httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": "  Multi-line\n\nOK.  "}]}}]},
        ),
    )
    out = await summarize_analyses("fake-key", [_sample_analysis()])
    assert "OK" in out
