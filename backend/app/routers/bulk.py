"""Bulk IOC job creation (M7)."""

from __future__ import annotations

import asyncio
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.auth.internal_jwt import InternalUser, get_current_internal_user
from app.deps import PoolDep
from app.schemas.bulk import BulkCreateIn, BulkJobCreated
from app.services.ioc.bulk_jobs import insert_bulk_job
from app.services.ioc.bulk_worker import run_bulk_job

router = APIRouter(tags=["ioc"])


@router.post("/ioc/bulk", response_model=BulkJobCreated)
async def create_bulk_job(
    body: BulkCreateIn,
    request: Request,
    pool: PoolDep,
    user: Annotated[InternalUser, Depends(get_current_internal_user)],
) -> BulkJobCreated:
    uid = UUID(user.user_id)
    job_id = await insert_bulk_job(pool, uid, body.iocs)
    asyncio.create_task(run_bulk_job(request.app, job_id, user.user_id))
    return BulkJobCreated(jobId=str(job_id), itemCount=len(body.iocs), status="pending")
