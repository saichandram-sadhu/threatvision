"""MISP restSearch + normalization for ThreatVision vendor row (spec §4.3, §4.10.8)."""

from __future__ import annotations

from typing import Any

from app.schemas.source_result import MispEventInfo, SourceResult, SourceVerdict
from app.services.misp.feed_map import feed_name_for_event, load_feed_lookup
from app.services.misp.http import misp_post_json


def _iter_attribute_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("response", "Attribute", "attributes", "data"):
            block = payload.get(key)
            if isinstance(block, list):
                return [x for x in block if isinstance(x, dict)]
            if isinstance(block, dict):
                return [block]
    return []


def _tags_from_event(ev: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for key in ("Tag", "EventTag"):
        block = ev.get(key)
        if not isinstance(block, list):
            continue
        for t in block:
            if isinstance(t, dict):
                name = t.get("name") or t.get("Name")
                if name:
                    out.append(str(name))
            elif isinstance(t, str):
                out.append(t)
    return out


def _tlp_from_tags(tags: list[str]) -> str:
    for t in tags:
        lower = t.lower()
        if lower.startswith("tlp:"):
            part = lower.split(":", 2)[-1].strip()
            if part in ("white", "green", "amber", "red"):
                return part.upper()
            if "amber" in part:
                return "AMBER"
    return "unknown"


def _event_title(ev: dict[str, Any]) -> str:
    info = ev.get("info") or ev.get("Info") or ev.get("title")
    if isinstance(info, str) and info.strip():
        return info.strip()
    eid = ev.get("id") or ev.get("Id")
    return f"Event {eid}" if eid is not None else "MISP event"


def group_events_from_restsearch_payload(
    payload: Any,
    feed_lookup: dict[str, str],
) -> list[MispEventInfo]:
    """Public helper for tests — parses MISP ``restSearch`` JSON into deduped events."""
    rows = _iter_attribute_rows(payload)
    return _group_events_from_attributes(rows, feed_lookup)


def _group_events_from_attributes(
    rows: list[dict[str, Any]],
    feed_lookup: dict[str, str],
) -> list[MispEventInfo]:
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        ev = row.get("Event")
        if not isinstance(ev, dict):
            continue
        eid = ev.get("id") or ev.get("Id")
        if eid is None:
            continue
        sid = str(eid)
        if sid not in by_id:
            tags = _tags_from_event(ev)
            fn = feed_name_for_event(ev, feed_lookup)
            by_id[sid] = {
                "eventId": sid,
                "eventName": _event_title(ev),
                "tags": tags,
                "tlp": _tlp_from_tags(tags),
                "feedName": fn,
            }
        else:
            extra = _tags_from_event(ev)
            merged = list(dict.fromkeys(by_id[sid]["tags"] + extra))
            by_id[sid]["tags"] = merged
            by_id[sid]["tlp"] = _tlp_from_tags(merged)
    return [MispEventInfo.model_validate(v) for v in by_id.values()]


async def search_misp_for_value(
    base_url: str,
    api_key: str,
    search_value: str,
) -> SourceResult:
    """Run ``attributes/restSearch`` and build the ``misp`` ``SourceResult``."""
    feed_lookup = await load_feed_lookup(base_url, api_key)
    body: dict[str, Any] = {
        "returnFormat": "json",
        "value": search_value,
        "enforceWarninglist": False,
        "includeEventTags": True,
        "includeCorrelations": False,
        "limit": 80,
    }
    try:
        payload = await misp_post_json(base_url, api_key, "/attributes/restSearch", body)
    except Exception as e:  # noqa: BLE001
        return SourceResult(
            id="misp",
            displayName="MISP",
            status="unavailable",
            verdict=None,
            detailLines=[],
            errorCode="http_error",
            metadata={"message": str(e)},
        )

    rows = _iter_attribute_rows(payload)
    events = _group_events_from_attributes(rows, feed_lookup)

    if not events:
        return SourceResult(
            id="misp",
            displayName="MISP",
            status="ok",
            verdict="clean",
            detailLines=["No matching attributes in your MISP instance."],
            metadata={"events": []},
        )

    detail_lines: list[str] = []
    feeds_named = [e.feedName for e in events if e.feedName]
    manual = sum(1 for e in events if not e.feedName)
    if len(feeds_named) == 1 and manual == 0:
        detail_lines.append(f"Found in: {feeds_named[0]}")
    elif len(feeds_named) > 0:
        uniq = list(dict.fromkeys(feeds_named))
        if len(uniq) <= 3:
            detail_lines.append("Found in: " + ", ".join(uniq))
        else:
            detail_lines.append(f"Found in: {len(uniq)} feeds")
        if manual:
            detail_lines.append(f"+ {manual} manual / unmatched events")
    elif manual:
        detail_lines.append(f"Found in: {len(events)} events (no feed mapping)")

    for e in events[:3]:
        tag_preview = ", ".join(e.tags[:5]) if e.tags else ""
        line = f"Event {e.eventId}: {e.eventName}"
        if e.tlp != "unknown":
            line += f" [TLP:{e.tlp}]"
        if tag_preview:
            line += f" — Tags: {tag_preview}"
        detail_lines.append(line)
    if len(events) > 3:
        detail_lines.append(f"+ {len(events) - 3} more events")

    verdict: SourceVerdict = "malicious"
    for e in events:
        if e.tlp == "WHITE":
            verdict = "suspicious"
            break

    return SourceResult(
        id="misp",
        displayName="MISP",
        status="ok",
        verdict=verdict,
        detailLines=detail_lines[:8],
        metadata={"events": [e.model_dump() for e in events]},
    )
