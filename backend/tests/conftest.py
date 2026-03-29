"""Pytest hooks and shared fixtures."""

from __future__ import annotations

import os

import pytest

from app.config import get_settings


def pytest_configure(config: pytest.Config) -> None:
    os.environ.setdefault(
        "INTERNAL_JWT_SECRET",
        "test-internal-jwt-secret-value-minimum-32-characters-long",
    )
    os.environ.setdefault(
        "BFF_SERVICE_KEY",
        "test-bff-service-key-shared-secret-for-pytest-only-32b",
    )
    os.environ.setdefault(
        "API_KEY_PEPPER",
        "test-api-key-pepper-secret-minimum-32-characters-long!",
    )
    os.environ.setdefault("SUPERADMIN_EMAIL", "superadmin@example.com")


@pytest.fixture(autouse=True)
def reset_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
