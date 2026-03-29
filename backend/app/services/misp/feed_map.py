"""Map MISP feed ids / URLs to display names (spec §4.10.8)."""

from __future__ import annotations

from typing import Any

from app.services.misp.explorer import parse_feeds_index
from app.services.misp.http import misp_get_json


async def load_feed_lookup(base_url: str, api_key: str) -> dict[str, str]:
    """
    Lowercased keys → feed display name.
    Keys: ``id:<id>``, ``url:<url>`` for fuzzy matching.
    """
    lookup: dict[str, str] = {}
    try:
        raw = await misp_get_json(base_url, api_key, "/feeds/index.json")
    except Exception:  # noqa: BLE001
        return lookup
    feeds = parse_feeds_index(raw)
    for f in feeds:
        name = f.name or "Feed"
        if f.id:
            lookup[f"id:{f.id}".lower()] = name
        if f.url:
            u = f.url.strip().rstrip("/").lower()
            lookup[f"url:{u}"] = name
            lookup[u] = name
    return lookup


def feed_name_for_event(event: dict[str, Any], lookup: dict[str, str]) -> str | None:
    """Best-effort feed label from event fields + lookup."""
    for key in ("feed_id", "Feed", "feedId"):
        v = event.get(key)
        if v is None:
            continue
        if isinstance(v, dict):
            fid = v.get("id") or v.get("Id")
            if fid is not None:
                hit = lookup.get(f"id:{str(fid)}".lower())
                if hit:
                    return hit
        else:
            hit = lookup.get(f"id:{str(v)}".lower())
            if hit:
                return hit

    for key in ("source", "Source", "event_source", "EventSource"):
        src = event.get(key)
        if isinstance(src, str) and src.strip():
            s = src.strip()
            hit = lookup.get(s.lower()) or lookup.get(f"url:{s.lower().rstrip('/')}")
            if hit:
                return hit

    orgc = event.get("Orgc") or event.get("orgc")
    if isinstance(orgc, dict):
        on = orgc.get("name") or orgc.get("Name")
        if isinstance(on, str) and on.strip():
            return f"Org: {on.strip()}"

    return None
