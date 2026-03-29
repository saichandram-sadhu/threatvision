"""Background processing for bulk IOC jobs."""

from __future__ import annotations

import logging
import uuid

import asyncpg
from fastapi import HTTPException
from starlette.applications import Starlette

from app.services.ioc.analyze import analyze_ioc_value
from app.services.ioc.bulk_hub import BulkStreamHub
from app.services.ioc.bulk_jobs import (
    claim_job_processing,
    fetch_job_items_ordered,
    mark_pending_items_rate_limited,
    set_job_status,
    update_item_done,
    update_item_error,
)
from app.services.rate_limit import check_and_increment_daily

log = logging.getLogger(__name__)


async def run_bulk_job(app: Starlette, job_id: uuid.UUID, user_id: str) -> None:
    pool: asyncpg.Pool | None = getattr(app.state, "pool", None)
    if pool is None:
        log.warning("bulk job %s skipped: no database pool", job_id)
        return

    hub: BulkStreamHub | None = getattr(app.state, "bulk_hub", None)
    job_key = str(job_id)
    uid = uuid.UUID(user_id)

    try:
        claimed = await claim_job_processing(pool, job_id)
        if not claimed:
            return

        items = await fetch_job_items_ordered(pool, job_id)
        total = len(items)
        if hub:
            await hub.publish(
                job_key,
                {"type": "progress", "done": 0, "total": total, "jobStatus": "processing"},
            )

        done = 0
        for row in items:
            if row["item_status"] != "pending":
                continue

            try:
                await check_and_increment_daily(pool, uid)
            except HTTPException as e:
                if e.status_code == 429:
                    await mark_pending_items_rate_limited(pool, job_id)
                    await set_job_status(pool, job_id, "failed")
                    if hub:
                        await hub.publish(
                            job_key,
                            {
                                "type": "done",
                                "jobStatus": "failed",
                                "total": total,
                                "reason": "rate_limit_exceeded",
                            },
                        )
                    return
                raise

            item_id = row["id"]
            raw = row["ioc_raw"]
            try:
                analysis = await analyze_ioc_value(
                    pool,
                    user_id=user_id,
                    raw_ioc=raw,
                    log_activity=False,
                )
            except Exception as exc:  # noqa: BLE001
                log.exception("bulk item failed job=%s item=%s", job_id, item_id)
                await update_item_error(pool, item_id, str(exc))
                if hub:
                    await hub.publish(
                        job_key,
                        {
                            "type": "item",
                            "position": row["position"],
                            "iocRaw": raw,
                            "error": str(exc)[:500],
                        },
                    )
                done += 1
                if hub:
                    await hub.publish(
                        job_key,
                        {
                            "type": "progress",
                            "done": done,
                            "total": total,
                            "jobStatus": "processing",
                        },
                    )
                continue

            payload = analysis.model_dump(mode="json")
            await update_item_done(
                pool,
                item_id,
                analysis.ioc.type,
                payload["aggregate"],
                [s for s in payload["sources"]],
            )
            done += 1
            if hub:
                await hub.publish(
                    job_key,
                    {
                        "type": "item",
                        "position": row["position"],
                        "result": payload,
                    },
                )
                await hub.publish(
                    job_key,
                    {
                        "type": "progress",
                        "done": done,
                        "total": total,
                        "jobStatus": "processing",
                    },
                )

        await set_job_status(pool, job_id, "complete")
        if hub:
            await hub.publish(
                job_key,
                {"type": "done", "jobStatus": "complete", "total": total},
            )
    except Exception as exc:  # noqa: BLE001
        log.exception("bulk job %s failed", job_id)
        try:
            await set_job_status(pool, job_id, "failed")
        except Exception:  # noqa: BLE001
            pass
        if hub:
            await hub.publish(
                job_key,
                {"type": "done", "jobStatus": "failed", "reason": str(exc)[:500]},
            )
