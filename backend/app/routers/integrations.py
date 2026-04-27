"""User integration settings: toggles, encrypted vendor keys, MISP (M14)."""

from __future__ import annotations

import json
import uuid
from typing import Annotated

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException

from app.auth.internal_jwt import InternalUser, get_current_internal_user
from app.deps import PoolDep
from app.schemas.integrations_settings import (
    EnricherProbeResult,
    IntegrationsGetOut,
    IntegrationsPutBody,
    IntegrationsPutOut,
    IntegrationSourceState,
    MispStateOut,
    TestEnrichersBody,
    TestEnrichersOut,
)
from app.services.crypto import CryptoError, decrypt_secret, encrypt_secret
from app.services.integrations.probes import run_probe_for_source
from app.services.integrations.secret_slots import normalize_secrets_dict
from app.services.ioc.integration_snapshot import (
    IntegrationSnapshot,
    load_integration_snapshot,
    parse_source_toggles,
    toggle_enabled,
)
from app.services.ioc.source_catalog import CATALOG_ORDER
from app.services.misp.resolve import normalize_misp_base_url, resolve_misp_for_user

router = APIRouter(tags=["integrations"])


@router.get("/settings/integrations", response_model=IntegrationsGetOut)
async def get_integrations(
    pool: PoolDep,
    user: Annotated[InternalUser, Depends(get_current_internal_user)],
) -> IntegrationsGetOut:
    uid = uuid.UUID(user.user_id)
    snapshot = await load_integration_snapshot(pool, user.user_id)
    row = await pool.fetchrow(
        """
        SELECT misp_base_url, misp_api_key_ciphertext
        FROM user_integration_settings
        WHERE user_id = $1
        """,
        uid,
    )
    misp_url = row["misp_base_url"] if row else None
    misp_key = bool(row and row["misp_api_key_ciphertext"])
    _bu, _bk, _tag = await resolve_misp_for_user(pool, user.user_id)
    explorer_available = bool(_bu and _bk)

    sources: list[IntegrationSourceState] = []
    for e in CATALOG_ORDER:
        if e.id == "misp":
            continue
        json_key: str | None = e.secret_key
        if e.id == "otx":
            json_key = "otx"
        elif not e.requires_api_key and e.id != "otx":
            json_key = None

        if json_key:
            configured = bool((snapshot.secrets.get(json_key) or "").strip())
        else:
            configured = True

        sources.append(
            IntegrationSourceState(
                id=e.id,
                display_name=e.display_name,
                requires_api_key=e.requires_api_key,
                enabled=toggle_enabled(snapshot, e.id, default=True),
                configured=configured,
                secret_key=json_key,
            )
        )

    return IntegrationsGetOut(
        misp=MispStateOut(
            base_url=misp_url,
            key_configured=misp_key,
            explorer_available=explorer_available,
        ),
        sources=sources,
    )


@router.put("/settings/integrations", response_model=IntegrationsPutOut)
async def put_integrations(
    body: IntegrationsPutBody,
    pool: PoolDep,
    user: Annotated[InternalUser, Depends(get_current_internal_user)],
) -> IntegrationsPutOut:
    uid = uuid.UUID(user.user_id)
    row = await pool.fetchrow(
        """
        SELECT source_toggles, secrets_ciphertext, misp_base_url, misp_api_key_ciphertext
        FROM user_integration_settings
        WHERE user_id = $1
        """,
        uid,
    )

    toggles: dict = {}
    secrets: dict[str, str] = {}
    misp_url: str | None = None
    misp_ct: str | None = None

    if row:
        toggles = parse_source_toggles(row["source_toggles"])
        misp_url = row["misp_base_url"]
        misp_ct = row["misp_api_key_ciphertext"]
    if row and row["secrets_ciphertext"]:
        try:
            raw = decrypt_secret(row["secrets_ciphertext"])
            data = json.loads(raw)
            if isinstance(data, dict):
                secrets = {str(k): str(v) for k, v in data.items() if v is not None}
        except (CryptoError, json.JSONDecodeError, TypeError):
            secrets = {}

    if body.source_toggles is not None:
        toggles = {**toggles, **body.source_toggles}

    if body.secrets is not None:
        for k, v in body.secrets.items():
            if v is not None and str(v).strip():
                secrets[str(k)] = str(v).strip()
    secrets = normalize_secrets_dict(secrets)

    if body.misp_base_url is not None and body.misp_base_url.strip():
        misp_url = normalize_misp_base_url(body.misp_base_url)

    if body.misp_api_key is not None and body.misp_api_key.strip():
        try:
            misp_ct = encrypt_secret(body.misp_api_key.strip())
        except CryptoError as e:
            raise HTTPException(
                status_code=503,
                detail="Cannot encrypt settings — check ENCRYPTION_KEY in backend environment.",
            ) from e

    secrets_json = json.dumps(secrets)
    try:
        secrets_blob = encrypt_secret(secrets_json)
    except CryptoError as e:
        raise HTTPException(
            status_code=503,
            detail="Cannot encrypt settings — check ENCRYPTION_KEY in backend environment.",
        ) from e

    await pool.execute(
        """
        INSERT INTO user_integration_settings (
            user_id, source_toggles, secrets_ciphertext, misp_base_url, misp_api_key_ciphertext, updated_at
        )
        VALUES ($1, $2::jsonb, $3, $4, $5, NOW())
        ON CONFLICT (user_id) DO UPDATE SET
            source_toggles = EXCLUDED.source_toggles,
            secrets_ciphertext = EXCLUDED.secrets_ciphertext,
            misp_base_url = EXCLUDED.misp_base_url,
            misp_api_key_ciphertext = EXCLUDED.misp_api_key_ciphertext,
            updated_at = NOW()
        """,
        uid,
        json.dumps(toggles),
        secrets_blob,
        misp_url,
        misp_ct,
    )

    return IntegrationsPutOut(saved_secret_slots=sorted(secrets.keys()))


@router.post("/settings/integrations/test-enrichers", response_model=TestEnrichersOut)
async def test_enrichers(
    pool: PoolDep,
    user: Annotated[InternalUser, Depends(get_current_internal_user)],
    body: Annotated[TestEnrichersBody, Body(default_factory=TestEnrichersBody)],
) -> TestEnrichersOut:
    snapshot = await load_integration_snapshot(pool, user.user_id)
    secrets = dict(snapshot.secrets)
    if body.secrets_override:
        for k, v in body.secrets_override.items():
            if v is not None and str(v).strip():
                secrets[str(k)] = str(v).strip()
    secrets = normalize_secrets_dict(secrets)

    toggles_snap = IntegrationSnapshot(snapshot.toggles, secrets)
    results: list[EnricherProbeResult] = []
    timeout = httpx.Timeout(connect=10.0, read=35.0, write=10.0, pool=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        for e in CATALOG_ORDER:
            if e.id == "misp":
                continue
            if body.source_id and e.id != body.source_id:
                continue
            if not toggle_enabled(toggles_snap, e.id, default=True):
                results.append(
                    EnricherProbeResult(
                        id=e.id,
                        display_name=e.display_name,
                        status="skipped",
                        detail="Disabled in toggles",
                    )
                )
                continue
            status, dname, detail = await run_probe_for_source(client, e.id, secrets)
            results.append(
                EnricherProbeResult(
                    id=e.id,
                    display_name=dname,
                    status=status,
                    detail=detail,
                )
            )

    return TestEnrichersOut(results=results)
