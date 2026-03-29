"""In-memory pub/sub for bulk job SSE (v1: single process)."""

from __future__ import annotations

import asyncio
from typing import Any


class BulkStreamHub:
    """Fan-out dict payloads to subscriber queues per job id (string UUID)."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._subs: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}

    async def subscribe(self, job_id: str) -> asyncio.Queue[dict[str, Any]]:
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        async with self._lock:
            self._subs.setdefault(job_id, []).append(q)
        return q

    async def unsubscribe(self, job_id: str, q: asyncio.Queue[dict[str, Any]]) -> None:
        async with self._lock:
            lst = self._subs.get(job_id)
            if not lst:
                return
            try:
                lst.remove(q)
            except ValueError:
                return
            if not lst:
                del self._subs[job_id]

    async def publish(self, job_id: str, payload: dict[str, Any]) -> None:
        async with self._lock:
            queues = list(self._subs.get(job_id, []))
        for q in queues:
            q.put_nowait(payload)
