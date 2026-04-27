"""MISP JSON parsers (fixture-driven)."""

from __future__ import annotations

import json
from pathlib import Path

from app.services.misp.explorer import (
    parse_feeds_index,
    parse_servers_index,
    parse_statistics,
    parse_taxonomies_index,
)

_FIX = Path(__file__).resolve().parent / "fixtures" / "misp"


def test_parse_feeds_index() -> None:
    data = json.loads((_FIX / "feeds_index.json").read_text(encoding="utf-8"))
    rows = parse_feeds_index(data)
    assert len(rows) == 2
    assert rows[0].name == "CIRCL OSINT Feed"
    assert rows[0].enabled is True
    assert rows[0].event_count == 42
    assert rows[1].enabled is False


def test_parse_servers_index() -> None:
    data = json.loads((_FIX / "servers_index.json").read_text(encoding="utf-8"))
    rows = parse_servers_index(data)
    assert len(rows) == 1
    assert rows[0].name == "partner-misp"
    assert rows[0].push is True
    assert rows[0].pull is True


def test_parse_taxonomies_index() -> None:
    data = json.loads((_FIX / "taxonomies_index.json").read_text(encoding="utf-8"))
    rows = parse_taxonomies_index(data)
    assert len(rows) == 2
    assert rows[0].namespace == "tlp"


def test_parse_statistics_nested() -> None:
    panel = parse_statistics(
        {
            "stats": {
                "event_count": 12847,
                "attribute_count": 900000,
                "object_count": 1200,
            }
        }
    )
    assert panel.total_events == 12847
    assert panel.total_attributes == 900000
    assert panel.total_objects == 1200


def test_parse_feeds_index_wrapped_feed_key() -> None:
    """MISP may return ``{"Feed": [ ... ]}`` instead of a bare list."""
    rows = parse_feeds_index(
        {
            "Feed": [
                {
                    "id": "9",
                    "name": "Test Feed",
                    "enabled": "1",
                    "event_count": 3,
                }
            ]
        }
    )
    assert len(rows) == 1
    assert rows[0].name == "Test Feed"
    assert rows[0].enabled is True
    assert rows[0].event_count == 3


def test_parse_feeds_index_empty_and_non_list() -> None:
    assert parse_feeds_index(None) == []
    assert parse_feeds_index({"feeds": "bad"}) == []


def test_parse_statistics_flat_event_keys() -> None:
    panel = parse_statistics({"event_count": 10, "attribute_count": 20, "object_count": 30})
    assert panel.total_events == 10
    assert panel.total_attributes == 20
    assert panel.total_objects == 30


def test_parse_servers_wrapped_servers_key() -> None:
    rows = parse_servers_index({"servers": [{"id": 1, "name": "local", "push": False, "pull": True}]})
    assert len(rows) == 1
    assert rows[0].name == "local"
    assert rows[0].push is False
    assert rows[0].pull is True
