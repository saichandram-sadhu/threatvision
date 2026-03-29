"""ThreatVision FastAPI application."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.pool import close_pool, create_pool
from app.routers import admin, auth, bulk, bulk_sse, internal, ioc, misp, reports, v1_me, webhooks
from app.services.ioc.bulk_hub import BulkStreamHub


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    pool = None
    if settings.database_url:
        pool = await create_pool(settings.database_url)
    app.state.pool = pool
    app.state.bulk_hub = BulkStreamHub()
    yield
    await close_pool(pool)


def create_application() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title="ThreatVision API", version="0.1.0", lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(webhooks.router)
    application.include_router(internal.router)
    application.include_router(auth.router)
    application.include_router(admin.router)
    application.include_router(misp.router)
    application.include_router(ioc.router)
    application.include_router(bulk.router)
    application.include_router(bulk_sse.router)
    application.include_router(reports.router)
    application.include_router(v1_me.router)

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_application()
