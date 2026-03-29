"""Report HTML + PDF helpers."""

from __future__ import annotations

import pytest

from app.schemas.source_result import AggregateResult, AnalyzeResponse, IocPayload, SourceResult
from app.services.reports.pdf import render_report_html


def _one_analysis() -> AnalyzeResponse:
    return AnalyzeResponse(
        ioc=IocPayload(raw="evil.example", normalized="evil.example", type="domain"),
        aggregate=AggregateResult(verdict="MALICIOUS", confidence=88, rationale="Sources agree"),
        sources=[
            SourceResult(
                id="misp",
                displayName="MISP",
                status="ok",
                verdict="malicious",
                detailLines=["Event 1: test"],
                metadata={
                    "events": [
                        {
                            "eventId": "99",
                            "eventName": "Phish",
                            "tags": ["tlp:amber"],
                            "tlp": "AMBER",
                            "feedName": "OSINT",
                        },
                    ],
                },
            ),
            SourceResult(
                id="virustotal",
                displayName="VirusTotal",
                status="not_configured",
                verdict=None,
                detailLines=[],
            ),
        ],
    )


def test_render_html_includes_branding_and_misp_block() -> None:
    html = render_report_html(
        analyses=[_one_analysis()],
        executive_summary="Paragraph one.\n\nParagraph two.",
    )
    assert "ThreatVision" in html
    assert "Saichandram Sadhu" in html
    assert "MISP events" in html
    assert "Event 99" in html
    assert "Executive summary" in html
    assert "Paragraph one" in html


@pytest.mark.asyncio
async def test_build_pdf_bytes_uses_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.reports.pdf.html_to_pdf_bytes", lambda h: b"%PDF-1.4 stub")
    from app.services.reports.pdf import build_pdf_bytes

    pdf = await build_pdf_bytes([_one_analysis()], "Summary")
    assert pdf.startswith(b"%PDF")
