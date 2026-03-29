"""Render HTML report and convert to PDF with WeasyPrint (M8)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.schemas.source_result import AnalyzeResponse, SourceResult

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def _verdict_row_classes(s: SourceResult) -> tuple[str, str]:
    if s.status == "not_configured":
        return "v-none", "NOT CONFIGURED"
    if s.status == "unavailable":
        return "v-none", "UNAVAILABLE"
    v = s.verdict
    if v == "malicious":
        return "v-malicious", "MALICIOUS"
    if v == "suspicious":
        return "v-suspicious", "SUSPICIOUS"
    if v == "clean":
        return "v-clean", "CLEAN"
    if v == "unknown":
        return "v-unknown", "UNKNOWN"
    return "v-none", "—"


def _analysis_blocks(analyses: list[AnalyzeResponse]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for a in analyses:
        misp_row = next((x for x in a.sources if x.id == "misp"), None)
        events: list[dict[str, Any]] = []
        if misp_row and isinstance(misp_row.metadata, dict):
            raw_ev = misp_row.metadata.get("events")
            if isinstance(raw_ev, list):
                for e in raw_ev:
                    if isinstance(e, dict):
                        events.append(
                            {
                                "eventId": str(e.get("eventId", "")),
                                "eventName": str(e.get("eventName", "")),
                                "tlp": str(e.get("tlp", "unknown")),
                                "feedName": e.get("feedName"),
                                "tags": e.get("tags") if isinstance(e.get("tags"), list) else [],
                            }
                        )
        vendor_rows = []
        for s in a.sources:
            vc, vl = _verdict_row_classes(s)
            vendor_rows.append(
                {
                    "name": s.displayName,
                    "verdict_class": vc,
                    "verdict_label": vl,
                    "detail_lines": list(s.detailLines or [])[:12],
                },
            )
        blocks.append(
            {
                "raw_display": a.ioc.raw[:500] + ("…" if len(a.ioc.raw) > 500 else ""),
                "normalized": a.ioc.normalized,
                "ioc_type": a.ioc.type,
                "agg_verdict": a.aggregate.verdict,
                "agg_confidence": a.aggregate.confidence,
                "agg_rationale": a.aggregate.rationale or "",
                "vendor_rows": vendor_rows,
                "misp_events": events[:24],
            },
        )
    return blocks


def _exec_paragraphs(summary: str) -> list[str]:
    parts = [p.strip() for p in summary.split("\n\n") if p.strip()]
    if parts:
        return parts
    s = summary.strip()
    return [s] if s else ["(No summary text.)"]


def render_report_html(
    *,
    analyses: list[AnalyzeResponse],
    executive_summary: str,
    generated_at: str | None = None,
) -> str:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    tpl = env.get_template("report.html")
    ts = generated_at or datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")
    return tpl.render(
        analyses=analyses,
        generated_at=ts,
        exec_paragraphs=_exec_paragraphs(executive_summary),
        analysis_blocks=_analysis_blocks(analyses),
    )


def html_to_pdf_bytes(html: str) -> bytes:
    try:
        from weasyprint import HTML
    except ImportError as e:  # pragma: no cover
        raise RuntimeError(
            "WeasyPrint is not available. Install system libraries (Cairo, Pango, GDK-Pixbuf) "
            "or use the Linux/Docker image documented in backend/README.md."
        ) from e
    return HTML(string=html, base_url=str(_TEMPLATES_DIR)).write_pdf()


async def build_pdf_bytes(
    analyses: list[AnalyzeResponse],
    executive_summary: str,
) -> bytes:
    html = render_report_html(analyses=analyses, executive_summary=executive_summary)
    return await asyncio.to_thread(html_to_pdf_bytes, html)
