"""ThreatVision FastAPI application."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.pool import close_pool, create_pool
from app.middleware.max_body import MaxRequestBodyMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routers import activity, admin, auth, bulk, bulk_sse, internal, integrations, ioc, misp, profile, reports, stats, v1_me, webhooks
from app.services.ioc.bulk_hub import BulkStreamHub

_log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    pool = None
    if settings.database_url:
        try:
            pool = await create_pool(settings.database_url, database_ssl=settings.database_ssl)
        except Exception as e:  # noqa: BLE001 — boot without DB when Docker/Postgres is down
            _log.warning(
                "PostgreSQL unreachable (%s); API starts without a pool. Run: docker compose up -d (threatvision/).",
                e,
            )
    app.state.pool = pool
    app.state.bulk_hub = BulkStreamHub()
    yield
    await close_pool(pool)


def create_application() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title="ThreatVision API", version="0.1.0", lifespan=lifespan)
    # Order: last added runs first on incoming requests — enforce size limit, then headers, then CORS.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(
        MaxRequestBodyMiddleware,
        max_content_length=settings.max_request_body_bytes,
    )
    application.include_router(webhooks.router)
    application.include_router(internal.router)
    application.include_router(auth.router)
    application.include_router(admin.router)
    application.include_router(misp.router)
    application.include_router(integrations.router)
    application.include_router(stats.router)
    application.include_router(activity.router)
    application.include_router(profile.router)
    application.include_router(ioc.router)
    application.include_router(bulk.router)
    application.include_router(bulk_sse.router)
    application.include_router(reports.router)
    application.include_router(v1_me.router)

    @application.get("/health")
    async def health(request: Request) -> dict[str, object]:
        """Lightweight liveness; when DB is up, reports whether platform MISP fallback is stored."""
        out: dict[str, object] = {"status": "ok", "pid": os.getpid()}
        pool = getattr(request.app.state, "pool", None)
        if pool is None:
            out["db"] = "disconnected"
            return out
        try:
            row = await pool.fetchrow(
                """
                SELECT
                    misp_fallback_url IS NOT NULL AND length(trim(misp_fallback_url)) > 0 AS has_url,
                    misp_fallback_api_key_ciphertext IS NOT NULL AS has_key_cipher
                FROM platform_settings
                WHERE id = 1
                """,
            )
            if row:
                out["platform_misp_configured"] = bool(row["has_url"] and row["has_key_cipher"])
            else:
                out["platform_misp_configured"] = False
        except Exception:  # noqa: BLE001 — health must not 500 if schema odd
            out["platform_misp_configured"] = False
        return out

    return application


app = create_application()
