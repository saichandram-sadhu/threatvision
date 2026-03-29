"""Server-Sent Events for bulk job progress (M7)."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.responses import StreamingResponse

from app.auth.internal_jwt import InternalUser, get_current_internal_user
from app.deps import PoolDep
from app.schemas.source_result import AggregateResult, AnalyzeResponse, IocPayload, SourceResult
from app.services.ioc.bulk_hub import BulkStreamHub
from app.services.ioc.bulk_jobs import fetch_job_items_ordered, get_job_for_user
from app.services.ioc.classify import classify_ioc

router = APIRouter(tags=["ioc"])
log = logging.getLogger(__name__)


def _sse_bytes(event: str, payload: dict[str, Any]) -> bytes:
    return f"event: {event}\ndata: {json.dumps(payload, separators=(',', ':'))}\n\n".encode("utf-8")


def _row_to_analyze_dict(row: Any) -> dict[str, Any]:
    t, n = classify_ioc(row["ioc_raw"])
    if row["ioc_type"]:
        t = str(row["ioc_type"])
    agg = row["aggregate"]
    src = row["sources"]
    if agg is None or src is None:
        raise ValueError("missing aggregate/sources")
    resp = AnalyzeResponse(
        ioc=IocPayload(raw=row["ioc_raw"], normalized=n, type=t),
        aggregate=AggregateResult.model_validate(agg),
        sources=[SourceResult.model_validate(x) for x in src],
    )
    return resp.model_dump(mode="json")


async def _replay_completed_rows(pool: Any, job_id: UUID) -> AsyncIterator[bytes]:
    rows = await fetch_job_items_ordered(pool, job_id)
    for row in rows:
        st = row["item_status"]
        pos = int(row["position"])
        if st == "done" and row["aggregate"] is not None and row["sources"] is not None:
            try:
                result = _row_to_analyze_dict(row)
            except Exception as exc:  # noqa: BLE001
                log.warning("bulk replay parse failed: %s", exc)
                yield _sse_bytes(
                    "item",
                    {
                        "type": "item",
                        "position": pos,
                        "iocRaw": row["ioc_raw"],
                        "error": "replay_parse_error",
                    },
                )
                continue
            yield _sse_bytes(
                "item",
                {"type": "item", "position": pos, "result": result},
            )
        elif st == "error":
            yield _sse_bytes(
                "item",
                {
                    "type": "item",
                    "position": pos,
                    "iocRaw": row["ioc_raw"],
                    "error": row["error_message"] or "error",
                },
            )


@router.get("/ioc/bulk/{job_id}/stream")
async def bulk_job_stream(
    job_id: UUID,
    request: Request,
    pool: PoolDep,
    user: Annotated[InternalUser, Depends(get_current_internal_user)],
) -> StreamingResponse:
    uid = UUID(user.user_id)
    job = await get_job_for_user(pool, job_id, uid)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    hub: BulkStreamHub | None = getattr(request.app.state, "bulk_hub", None)

    async def event_iterator() -> AsyncIterator[bytes]:
        q: asyncio.Queue[dict[str, Any]] | None = None
        try:
            async for chunk in _replay_completed_rows(pool, job_id):
                yield chunk

            rows = await fetch_job_items_ordered(pool, job_id)
            total = len(rows)
            j = await get_job_for_user(pool, job_id, uid)
            if j and j["status"] in ("complete", "failed"):
                yield _sse_bytes(
                    "done",
                    {
                        "type": "done",
                        "jobStatus": j["status"],
                        "total": total,
                    },
                )
                return

            if hub is None:
                yield _sse_bytes(
                    "done",
                    {
                        "type": "done",
                        "jobStatus": "failed",
                        "reason": "sse_hub_unavailable",
                        "total": total,
                    },
                )
                return

            q = await hub.subscribe(str(job_id))
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg: dict[str, Any] = await asyncio.wait_for(q.get(), timeout=25.0)
                except asyncio.TimeoutError:
                    yield _sse_bytes("ping", {})
                    j3 = await get_job_for_user(pool, job_id, uid)
                    if j3 and j3["status"] in ("complete", "failed"):
                        yield _sse_bytes(
                            "done",
                            {
                                "type": "done",
                                "jobStatus": j3["status"],
                                "total": total,
                            },
                        )
                        break
                    continue

                mtype = msg.get("type")
                if mtype == "progress":
                    yield _sse_bytes("progress", msg)
                elif mtype == "item":
                    yield _sse_bytes("item", msg)
                elif mtype == "done":
                    yield _sse_bytes("done", msg)
                    break
        finally:
            if hub is not None and q is not None:
                await hub.unsubscribe(str(job_id), q)

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(event_iterator(), media_type="text/event-stream", headers=headers)
