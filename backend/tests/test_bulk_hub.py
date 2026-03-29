"""Bulk SSE hub."""

from __future__ import annotations

import asyncio

import pytest

from app.services.ioc.bulk_hub import BulkStreamHub


@pytest.mark.asyncio
async def test_hub_publish_delivers_to_subscriber() -> None:
    hub = BulkStreamHub()
    q = await hub.subscribe("job-1")
    await hub.publish("job-1", {"type": "progress", "done": 1})
    msg = await asyncio.wait_for(q.get(), timeout=2.0)
    assert msg["type"] == "progress"
    assert msg["done"] == 1
    await hub.unsubscribe("job-1", q)


@pytest.mark.asyncio
async def test_hub_unsubscribe_stops_delivery() -> None:
    hub = BulkStreamHub()
    q = await hub.subscribe("job-2")
    await hub.unsubscribe("job-2", q)
    await hub.publish("job-2", {"type": "item"})
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(q.get(), timeout=0.2)
