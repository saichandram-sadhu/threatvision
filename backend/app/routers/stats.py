"""Per-user dashboard statistics from activity_log (M13)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.auth.internal_jwt import InternalUser, get_current_internal_user
from app.deps import PoolDep
from app.schemas.stats import DashboardStatsResponse, TopIpRow, VerdictBucket

router = APIRouter(tags=["stats"])


@router.get("/stats/dashboard", response_model=DashboardStatsResponse)
async def dashboard_stats(
    pool: PoolDep,
    user: Annotated[InternalUser, Depends(get_current_internal_user)],
) -> DashboardStatsResponse:
    uid = uuid.UUID(user.user_id)

    row = await pool.fetchrow(
        """
        SELECT
            COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '1 day') AS analyses_1d,
            COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') AS analyses_7d,
            COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') AS analyses_30d,
            COUNT(*) AS analyses_all
        FROM activity_log
        WHERE user_id = $1
        """,
        uid,
    )
    assert row is not None

    verdict_rows = await pool.fetch(
        """
        SELECT verdict, COUNT(*)::bigint AS count
        FROM activity_log
        WHERE user_id = $1 AND created_at >= NOW() - INTERVAL '30 days'
        GROUP BY verdict
        ORDER BY count DESC
        """,
        uid,
    )

    ip_rows = await pool.fetch(
        """
        SELECT ioc_snippet AS ip, COUNT(*)::bigint AS count
        FROM activity_log
        WHERE user_id = $1
          AND created_at >= NOW() - INTERVAL '30 days'
          AND ioc_snippet ~ '^([0-9]{1,3}\\.){3}[0-9]{1,3}$'
        GROUP BY ioc_snippet
        ORDER BY count DESC
        LIMIT 10
        """,
        uid,
    )

    return DashboardStatsResponse(
        analyses_1d=int(row["analyses_1d"]),
        analyses_7d=int(row["analyses_7d"]),
        analyses_30d=int(row["analyses_30d"]),
        analyses_all=int(row["analyses_all"]),
        verdict_distribution_30d=[
            VerdictBucket(verdict=str(r["verdict"]), count=int(r["count"])) for r in verdict_rows
        ],
        top_ips_30d=[TopIpRow(ip=str(r["ip"]), count=int(r["count"])) for r in ip_rows],
    )
