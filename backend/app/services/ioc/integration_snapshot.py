"""User integration toggles + decrypted secrets blob (JSON object)."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

import asyncpg

from app.services.crypto import CryptoError, decrypt_secret


@dataclass
class IntegrationSnapshot:
    toggles: dict[str, bool]
    secrets: dict[str, str]


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
    toggles = row["source_toggles"] or {}
    if not isinstance(toggles, dict):
        toggles = {}
    secrets: dict[str, str] = {}
    ct = row["secrets_ciphertext"]
    if ct:
        try:
            raw = decrypt_secret(ct)
            data = json.loads(raw)
            if isinstance(data, dict):
                secrets = {str(k): str(v) for k, v in data.items() if v is not None}
        except (CryptoError, json.JSONDecodeError, TypeError):
            secrets = {}
    return IntegrationSnapshot(toggles, secrets)


def toggle_enabled(snapshot: IntegrationSnapshot, source_id: str, *, default: bool = True) -> bool:
    v = snapshot.toggles.get(source_id)
    if v is None:
        return default
    return bool(v)
