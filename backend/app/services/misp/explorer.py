"""Aggregate MISP Instance Explorer data (spec §4.10)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.schemas.misp_explorer import (
    MispExplorerResponse,
    MispFeedRow,
    MispServerRow,
    MispStatsPanel,
    MispTaxonomyRow,
)
from app.services.misp.http import misp_get_json, misp_ping_version


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=UTC)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(s)
            return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
        except ValueError:
            return None
    if isinstance(value, dict):
        for k in ("time", "timestamp", "Time"):
            if k in value:
                return _parse_dt(value[k])
    return None


def _coerce_bool(v: Any) -> bool | None:
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    if isinstance(v, str):
        return v.lower() in ("1", "true", "yes", "on")
    return None


def parse_feeds_index(data: Any) -> list[MispFeedRow]:
    rows: list[MispFeedRow] = []
    if data is None:
        return rows
    items: Any = data
    if isinstance(data, dict):
        for key in ("Feed", "feeds", "response"):
            if key in data:
                items = data[key]
                break
    if not isinstance(items, list):
        return rows
    for raw in items:
        if not isinstance(raw, dict):
            continue
        fid = raw.get("id") or raw.get("Id")
        last_fetch = _parse_dt(
            raw.get("last_fetch")
            or raw.get("lastfetched")
            or raw.get("timestamp")
            or raw.get("last_try")
        )
        enabled = _coerce_bool(raw.get("enabled"))
        fmt = raw.get("format") or raw.get("source_format") or raw.get("type") or raw.get("input_source")
        if isinstance(fmt, dict):
            fmt = fmt.get("name") or fmt.get("type")
        fmt_s = str(fmt) if fmt is not None else None
        cache_age = None
        if last_fetch:
            cache_age = max(0, int((datetime.now(tz=UTC) - last_fetch).total_seconds()))
        rows.append(
            MispFeedRow(
                id=str(fid) if fid is not None else None,
                name=raw.get("name") or raw.get("Name"),
                url=raw.get("url") or raw.get("Url") or raw.get("source"),
                source_format=fmt_s,
                enabled=enabled,
                last_fetch=last_fetch,
                event_count=_safe_int(raw.get("event_count") or raw.get("events_count")),
                live_sync=enabled,
                cache_age_seconds=cache_age,
            )
        )
    return rows


def parse_servers_index(data: Any) -> list[MispServerRow]:
    rows: list[MispServerRow] = []
    if data is None:
        return rows
    items: Any = data
    if isinstance(data, dict):
        for key in ("Server", "servers", "response"):
            if key in data:
                items = data[key]
                break
    if not isinstance(items, list):
        return rows
    for raw in items:
        if not isinstance(raw, dict):
            continue
        sid = raw.get("id") or raw.get("Id")
        push = _coerce_bool(raw.get("push"))
        pull = _coerce_bool(raw.get("pull"))
        last = _parse_dt(raw.get("last_pushed") or raw.get("last_pull") or raw.get("last_sync"))
        status = raw.get("status") or raw.get("connection_status")
        if isinstance(status, dict):
            status = status.get("text") or status.get("name")
        rows.append(
            MispServerRow(
                id=str(sid) if sid is not None else None,
                name=raw.get("name") or raw.get("Name"),
                url=raw.get("url") or raw.get("Url") or raw.get("baseurl"),
                push=push,
                pull=pull,
                last_sync=last,
                sync_status=str(status).lower() if status is not None else None,
                event_count=_safe_int(raw.get("event_count")),
            )
        )
    return rows


def parse_taxonomies_index(data: Any) -> list[MispTaxonomyRow]:
    rows: list[MispTaxonomyRow] = []
    if data is None:
        return rows
    items: Any = data
    if isinstance(data, dict):
        for key in ("Taxonomy", "taxonomies", "response"):
            if key in data:
                items = data[key]
                break
    if not isinstance(items, list):
        return rows
    for raw in items:
        if not isinstance(raw, dict):
            continue
        ns = raw.get("namespace") or raw.get("Namespace") or raw.get("tag")
        rows.append(
            MispTaxonomyRow(
                namespace=str(ns) if ns is not None else None,
                enabled=_coerce_bool(raw.get("enabled")),
                description=raw.get("description") or raw.get("Description"),
            )
        )
    return rows


def _safe_int(v: Any) -> int | None:
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def parse_statistics(data: Any) -> MispStatsPanel:
    panel = MispStatsPanel()
    if not isinstance(data, dict):
        return panel
    block: dict[str, Any] | None = data
    for k in ("stats", "Stats", "database", "Database"):
        inner = data.get(k)
        if isinstance(inner, dict):
            block = inner
            break
    if block is None:
        return panel
    panel.total_events = _safe_int(block.get("event_count") or block.get("events"))
    panel.total_attributes = _safe_int(block.get("attribute_count") or block.get("attributes"))
    panel.total_objects = _safe_int(block.get("object_count") or block.get("objects"))
    panel.last_event_added = _parse_dt(block.get("last_event") or block.get("latest_event_created"))
    return panel


def _sync_indicator(source_errors: dict[str, str], feeds: list[MispFeedRow]) -> str:
    if "version" in source_errors:
        return "error"
    now = datetime.now(tz=UTC)
    for f in feeds:
        if f.enabled and f.last_fetch:
            if (now - f.last_fetch).total_seconds() < 600:
                return "syncing"
    return "idle"


async def build_explorer_snapshot(
    base_url: str,
    api_key: str,
    *,
    resolution: str = "user",
) -> MispExplorerResponse:
    errors: dict[str, str] = {}
    version_str: str | None = None

    try:
        vp = await misp_ping_version(base_url, api_key)
        if isinstance(vp, dict):
            version_str = str(vp.get("version") or vp.get("Version") or "") or None
    except Exception as e:  # noqa: BLE001
        errors["version"] = str(e)

    feeds_raw = None
    try:
        feeds_raw = await misp_get_json(base_url, api_key, "/feeds/index.json")
    except Exception as e:  # noqa: BLE001
        errors["feeds"] = str(e)
    feeds = parse_feeds_index(feeds_raw)

    servers_raw = None
    try:
        servers_raw = await misp_get_json(base_url, api_key, "/servers/index.json")
    except Exception as e:  # noqa: BLE001
        errors["servers"] = str(e)
    servers = parse_servers_index(servers_raw)

    tax_raw = None
    try:
        tax_raw = await misp_get_json(base_url, api_key, "/taxonomies/index.json")
    except Exception as e:  # noqa: BLE001
        errors["taxonomies"] = str(e)
    taxonomies = parse_taxonomies_index(tax_raw)

    try:
        stats_raw = await misp_get_json(base_url, api_key, "/users/statistics.json")
        stats_panel = parse_statistics(stats_raw)
    except Exception:  # noqa: BLE001
        stats_panel = MispStatsPanel()
    stats_panel.misp_version = version_str or stats_panel.misp_version
    stats_panel.feeds_configured = len(feeds)
    stats_panel.feeds_enabled = sum(1 for f in feeds if f.enabled)
    stats_panel.connected_servers = len(servers)

    return MispExplorerResponse(
        connected="version" not in errors,
        base_url=base_url,
        resolution=resolution,
        misp_version=version_str,
        feeds=feeds,
        servers=servers,
        taxonomies=taxonomies,
        stats=stats_panel,
        sync_indicator=_sync_indicator(errors, feeds),
        source_errors=errors,
        fetched_at=datetime.now(tz=UTC),
    )
