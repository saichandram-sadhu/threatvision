"""User integrations form DTOs (M14)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class IntegrationSourceState(BaseModel):
    id: str
    display_name: str
    requires_api_key: bool
    enabled: bool
    configured: bool
    secret_key: str | None = Field(
        default=None,
        description="JSON secrets blob key for this row's input; None if no API key field.",
    )


class MispStateOut(BaseModel):
    base_url: str | None = None
    key_configured: bool = False
    explorer_available: bool = Field(
        default=False,
        description="True when URL+key resolve (user settings, platform fallback, or env/.env).",
    )


class IntegrationsGetOut(BaseModel):
    misp: MispStateOut
    sources: list[IntegrationSourceState] = Field(default_factory=list)


class IntegrationsPutBody(BaseModel):
    """Non-empty ``secrets`` values overwrite that key; omitted keys are unchanged."""

    model_config = ConfigDict(extra="ignore")

    misp_base_url: str | None = None
    misp_api_key: str | None = Field(default=None, description="Omit or empty to keep existing key")
    source_toggles: dict[str, bool] | None = None
    secrets: dict[str, str] | None = None


class IntegrationsPutOut(BaseModel):
    saved: bool = True
    saved_secret_slots: list[str] = Field(
        default_factory=list,
        description="Canonical secret slot ids stored after this save (names only).",
    )


class EnricherProbeResult(BaseModel):
    id: str
    display_name: str
    status: str = Field(description="ok | failed | skipped | not_configured")
    detail: str | None = None


class TestEnrichersBody(BaseModel):
    """Optional inline secrets merged over DB for probing only (not saved)."""

    secrets_override: dict[str, str] | None = None
    source_id: str | None = None


class TestEnrichersOut(BaseModel):
    results: list[EnricherProbeResult] = Field(default_factory=list)
