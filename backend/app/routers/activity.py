"""Recent IOC activity for dashboard (M13)."""

from __future__ import annotations

import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.auth.internal_jwt import InternalUser, get_current_internal_user
from app.deps import PoolDep
from app.schemas.activity_recent import ActivityRecentItem, ActivityRecentResponse, FlaggedByChip
from app.services.ioc.source_catalog import display_name_for_source_id

router = APIRouter(tags=["activity"])


@router.get("/activity/recent", response_model=ActivityRecentResponse)
async def activity_recent(
    pool: PoolDep,
    user: Annotated[InternalUser, Depends(get_current_internal_user)],
    limit: int = Query(30, ge=1, le=100),
) -> ActivityRecentResponse:
    uid = uuid.UUID(user.user_id)
    rows = await pool.fetch(
        """
        SELECT id, ioc_snippet, verdict, flagged_by, created_at
        FROM activity_log
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT $2
        """,
        uid,
        limit,
    )

    items: list[ActivityRecentItem] = []
    for r in rows:
        raw_fb = r["flagged_by"]
        if isinstance(raw_fb, str):
            ids: list[str] = json.loads(raw_fb)
        elif raw_fb is None:
            ids = []
        else:
            ids = list(raw_fb)
        chips = [FlaggedByChip(id=i, display_name=display_name_for_source_id(str(i))) for i in ids]
        items.append(
            ActivityRecentItem(
                id=str(r["id"]),
                ioc_snippet=str(r["ioc_snippet"]),
                verdict=str(r["verdict"]),
                created_at=r["created_at"],
                flagged_by=chips,
            )
        )

    return ActivityRecentResponse(items=items)
