"""Production safety validators on Settings."""

from __future__ import annotations

import pytest

from app.config import get_settings


def test_development_allows_dev_quick_admin_when_env_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("DEV_QUICK_ADMIN_LOGIN", "true")
    monkeypatch.setenv("INTERNAL_JWT_SECRET", "test-internal-jwt-secret-value-minimum-32-characters-long")
    monkeypatch.setenv("BFF_SERVICE_KEY", "test-bff-service-key-shared-secret-for-pytest-only-32b")
    monkeypatch.setenv("API_KEY_PEPPER", "test-api-key-pepper-secret-minimum-32-characters-long!")
    monkeypatch.setenv("SUPERADMIN_EMAIL", "superadmin@example.com")
    get_settings.cache_clear()
    s = get_settings()
    assert s.dev_quick_admin_login is True


def test_production_environment_forces_dev_quick_admin_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DEV_QUICK_ADMIN_LOGIN", "true")
    monkeypatch.setenv("INTERNAL_JWT_SECRET", "test-internal-jwt-secret-value-minimum-32-characters-long")
    monkeypatch.setenv("BFF_SERVICE_KEY", "test-bff-service-key-shared-secret-for-pytest-only-32b")
    monkeypatch.setenv("API_KEY_PEPPER", "test-api-key-pepper-secret-minimum-32-characters-long!")
    monkeypatch.setenv("SUPERADMIN_EMAIL", "superadmin@example.com")
    get_settings.cache_clear()
    s = get_settings()
    assert s.dev_quick_admin_login is False
