"""Shared context passed to each enricher."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import httpx

from app.services.ioc.classify import IocType
from app.services.ioc.integration_snapshot import IntegrationSnapshot

if TYPE_CHECKING:
    pass


@dataclass
class EnricherContext:
    ioc_type: IocType
    normalized: str
    raw_ioc: str
    snapshot: IntegrationSnapshot
    client: httpx.AsyncClient
