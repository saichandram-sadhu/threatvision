"""Google Gemini executive summary for PDF reports (M8)."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.schemas.source_result import AnalyzeResponse

log = logging.getLogger(__name__)

PLACEHOLDER_FAILURE = (
    "Executive summary unavailable (AI service did not respond). "
    "Per-source results in this report are unchanged."
)

PLACEHOLDER_NO_KEY = (
    "Executive summary is not configured (no GEMINI_API_KEY). "
    "Refer to the per-vendor tables below for authoritative findings."
)

_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent"
)

_SAFETY = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]


def _brief_for_prompt(analyses: list[AnalyzeResponse]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for a in analyses:
        sources_brief = [
            {
                "name": s.displayName,
                "id": s.id,
                "status": s.status,
                "verdict": s.verdict,
                "lines": s.detailLines[:4],
            }
            for s in a.sources
        ]
        misp_meta = next((s.metadata for s in a.sources if s.id == "misp"), {})
        events = misp_meta.get("events") if isinstance(misp_meta, dict) else None
        out.append(
            {
                "ioc": {
                    "raw": a.ioc.raw,
                    "normalized": a.ioc.normalized,
                    "type": a.ioc.type,
                },
                "aggregate": {
                    "verdict": a.aggregate.verdict,
                    "confidence": a.aggregate.confidence,
                    "rationale": a.aggregate.rationale,
                },
                "sources": sources_brief,
                "misp_event_count": len(events) if isinstance(events, list) else 0,
            },
        )
    return out


async def summarize_analyses(api_key: str | None, analyses: list[AnalyzeResponse]) -> str:
    """
    Return a short executive summary referencing sources that agreed (by name only).
    Never invent vendors beyond those present in the brief.
    """
    if not analyses:
        return PLACEHOLDER_FAILURE
    if not (api_key or "").strip():
        return PLACEHOLDER_NO_KEY

    brief = _brief_for_prompt(analyses)
    prompt = (
        "You are writing the executive summary for a threat intelligence analyst report.\n"
        "Rules:\n"
        "- Reference only intelligence sources named in the JSON (by display name).\n"
        "- Do not invent vendors, feeds, or IOCs.\n"
        "- Call out agreement or tension between sources when multiple ran.\n"
        "- Keep to 2–4 short paragraphs, professional tone.\n"
        "- IOC data may be malicious; describe risk factually.\n\n"
        "Analysis JSON:\n"
        f"{json.dumps(brief, indent=2)[:24000]}"
    )

    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.35,
            "maxOutputTokens": 1024,
        },
        "safetySettings": _SAFETY,
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(45.0)) as client:
            r = await client.post(
                _GEMINI_URL,
                params={"key": api_key.strip()},
                json=body,
                headers={"Content-Type": "application/json"},
            )
            r.raise_for_status()
            data = r.json()
            cand = (data.get("candidates") or [None])[0]
            if not cand:
                log.warning("gemini: empty candidates: %s", data)
                return PLACEHOLDER_FAILURE
            content = cand.get("content") or {}
            parts = content.get("parts") or []
            text = ""
            for p in parts:
                if isinstance(p, dict) and p.get("text"):
                    text += str(p["text"])
            text = text.strip()
            if not text:
                log.warning("gemini: no text in parts")
                return PLACEHOLDER_FAILURE
            return text
    except httpx.HTTPStatusError as e:
        log.warning("gemini http error: %s %s", e.response.status_code, e.response.text[:300])
        return PLACEHOLDER_FAILURE
    except Exception as e:  # noqa: BLE001
        log.warning("gemini request failed: %s", e)
        return PLACEHOLDER_FAILURE
