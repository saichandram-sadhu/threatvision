"""User integration toggles + decrypted secrets blob (JSON object)."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

import asyncpg

from app.services.crypto import CryptoError, decrypt_secret
from app.services.integrations.secret_slots import normalize_secrets_dict


@dataclass
class IntegrationSnapshot:
    toggles: dict[str, bool]
    secrets: dict[str, str]


def parse_source_toggles(raw: object) -> dict[str, bool]:
    """asyncpg may return ``jsonb`` as ``dict`` or as a JSON ``str`` depending on codec/version."""
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return {str(k): bool(v) for k, v in raw.items()}
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return {}
        try:
            data = json.loads(s)
        except json.JSONDecodeError:
            return {}
        if not isinstance(data, dict):
            return {}
        return {str(k): bool(v) for k, v in data.items()}
    return {}


async def load_integration_snapshot(pool: asyncpg.Pool, user_id: str) -> IntegrationSnapshot:
    uid = uuid.UUID(user_id)
    row = await pool.fetchrow(
        """
        SELECT source_toggles, secrets_ciphertext
        FROM user_integration_settings
        WHERE user_id = $1
        """,
        uid,
    )
    if row is None:
        return IntegrationSnapshot({}, {})
    toggles = parse_source_toggles(row["source_toggles"])
    secrets: dict[str, str] = {}
    ct = row["secrets_ciphertext"]
    if ct:
        try:
            raw = decrypt_secret(ct)
            data = json.loads(raw)
            if isinstance(data, dict):
                secrets = {str(k): str(v) for k, v in data.items() if v is not None}
                secrets = normalize_secrets_dict(secrets)
        except (CryptoError, json.JSONDecodeError, TypeError):
            secrets = {}
    return IntegrationSnapshot(toggles, secrets)


def toggle_enabled(snapshot: IntegrationSnapshot, source_id: str, *, default: bool = True) -> bool:
    v = snapshot.toggles.get(source_id)
    if v is None:
        return default
    return bool(v)
