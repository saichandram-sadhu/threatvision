"""SIEM inbound webhooks (Wazuh + generic JSON) — M9."""

from __future__ import annotations

import json
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.config import Settings, get_settings_dep
from app.deps import PoolDep
from app.schemas.siem import SiemIocResult, SiemWebhookResult
from app.services.ioc.analyze import analyze_ioc_value
from app.services.rate_limit import check_and_increment_daily
from app.services.siem.extract_iocs import extract_ioc_strings
from app.services.siem.webhook_verify import authenticate_webhook, fetch_webhook_by_path_key

router = APIRouter(prefix="/api/webhook", tags=["webhooks"])
log = logging.getLogger(__name__)


async def _siem_webhook_core(
    path_key: str,
    request: Request,
    pool: PoolDep,
    settings: Settings,
    x_tv_webhook_secret: str | None,
    x_tv_timestamp: str | None,
    x_tv_signature: str | None,
) -> SiemWebhookResult:
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Empty body")

    row = await fetch_webhook_by_path_key(pool, path_key.strip())
    if row is None:
        raise HTTPException(status_code=404, detail="Unknown webhook endpoint")

    authenticate_webhook(
        row,
        settings,
        webhook_secret_header=x_tv_webhook_secret,
        timestamp_header=x_tv_timestamp,
        signature_hex=x_tv_signature,
        body=body,
    )

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from e
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="JSON object required at root")

    candidates = extract_ioc_strings(payload)
    if not candidates:
        return SiemWebhookResult(
            accepted=True,
            iocCount=0,
            analyzed=0,
            results=[],
            message="No IOC candidates found",
        )

    results: list[SiemIocResult] = []
    for raw in candidates:
        try:
            await check_and_increment_daily(pool, UUID(row.user_id))
        except HTTPException as e:
            if e.status_code == 429:
                return SiemWebhookResult(
                    accepted=True,
                    iocCount=len(candidates),
                    analyzed=sum(1 for r in results if r.error is None),
                    results=results,
                    message="Rate limit reached; remaining IOCs were not analyzed",
                )
            raise
        try:
            ar = await analyze_ioc_value(
                pool,
                user_id=row.user_id,
                raw_ioc=raw,
                log_activity=True,
            )
            results.append(
                SiemIocResult(
                    ioc=raw,
                    normalized=ar.ioc.normalized,
                    type=ar.ioc.type,
                    verdict=ar.aggregate.verdict,
                    confidence=ar.aggregate.confidence,
                ),
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("siem webhook analyze failed for %s", raw[:80])
            results.append(SiemIocResult(ioc=raw, error=str(exc)[:500]))

    ok = sum(1 for r in results if r.error is None)
    return SiemWebhookResult(
        accepted=True,
        iocCount=len(candidates),
        analyzed=ok,
        results=results,
    )


@router.post("/siem/{path_key}", response_model=SiemWebhookResult)
async def siem_webhook_path(
    path_key: str,
    request: Request,
    pool: PoolDep,
    settings: Annotated[Settings, Depends(get_settings_dep)],
    x_tv_webhook_secret: Annotated[str | None, Header()] = None,
    x_tv_timestamp: Annotated[str | None, Header()] = None,
    x_tv_signature: Annotated[str | None, Header()] = None,
) -> SiemWebhookResult:
    return await _siem_webhook_core(
        path_key,
        request,
        pool,
        settings,
        x_tv_webhook_secret,
        x_tv_timestamp,
        x_tv_signature,
    )


@router.post("/siem", response_model=SiemWebhookResult)
async def siem_webhook_header_path(
    request: Request,
    pool: PoolDep,
    settings: Annotated[Settings, Depends(get_settings_dep)],
    x_tv_path_key: Annotated[str | None, Header()] = None,
    x_tv_webhook_secret: Annotated[str | None, Header()] = None,
    x_tv_timestamp: Annotated[str | None, Header()] = None,
    x_tv_signature: Annotated[str | None, Header()] = None,
) -> SiemWebhookResult:
    if not x_tv_path_key or not x_tv_path_key.strip():
        raise HTTPException(
            status_code=400,
            detail="Provide path_key in the URL (/api/webhook/siem/{path_key}) or X-Tv-Path-Key header",
        )
    return await _siem_webhook_core(
        x_tv_path_key.strip(),
        request,
        pool,
        settings,
        x_tv_webhook_secret,
        x_tv_timestamp,
        x_tv_signature,
    )
