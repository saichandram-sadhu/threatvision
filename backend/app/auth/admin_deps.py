"""Superadmin-only dependency (JWT role + DB role + env email match)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException

from app.auth.internal_jwt import InternalUser, get_current_internal_user
from app.config import Settings, get_settings_dep
from app.deps import PoolDep


async def require_superadmin(
    internal: Annotated[InternalUser, Depends(get_current_internal_user)],
    pool: PoolDep,
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> InternalUser:
    try:
        uid = uuid.UUID(internal.user_id)
    except ValueError as e:
        raise HTTPException(status_code=403, detail="Invalid user reference") from e

    row = await pool.fetchrow(
        """
        SELECT email, role::text AS role, banned
        FROM users
        WHERE id = $1
        """,
        uid,
    )
    if row is None:
        raise HTTPException(status_code=403, detail="User not found")
    if row["banned"]:
        raise HTTPException(status_code=403, detail="Account disabled")
    if internal.role != "SUPERADMIN" or row["role"] != "SUPERADMIN":
        raise HTTPException(status_code=403, detail="Superadmin role required")
    env_email = settings.superadmin_email.strip().lower()
    if row["email"].strip().lower() != env_email:
        raise HTTPException(status_code=403, detail="Superadmin email does not match platform configuration")
    return internal
