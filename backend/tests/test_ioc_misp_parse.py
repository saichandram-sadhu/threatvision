"""MISP restSearch payload parsing."""

from __future__ import annotations

import json
from pathlib import Path

from app.services.misp.ioc_search import group_events_from_restsearch_payload

_FIX = Path(__file__).resolve().parent / "fixtures" / "misp"


def test_group_events_dedupes_and_merges_tags() -> None:
    payload = json.loads((_FIX / "restsearch_attributes.json").read_text(encoding="utf-8"))
    events = group_events_from_restsearch_payload(payload, {})
    assert len(events) == 1
    e = events[0]
    assert e.eventId == "5001"
    assert "Suspicious" in e.eventName
    assert e.tlp == "AMBER"
    assert any("APT1" in t for t in e.tags)
    assert e.feedName == "Org: Test Org"
