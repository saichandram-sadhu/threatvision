"""Fernet crypto for integration secrets."""

from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from app.services.crypto import CryptoError, decrypt_secret, encrypt_secret


def test_encrypt_decrypt_roundtrip() -> None:
    key = Fernet.generate_key().decode("ascii")
    secret = '{"virustotal":"abc123"}'
    token = encrypt_secret(secret, key=key)
    assert token != secret
    assert decrypt_secret(token, key=key) == secret


def test_decrypt_wrong_key_raises() -> None:
    k1 = Fernet.generate_key().decode("ascii")
    k2 = Fernet.generate_key().decode("ascii")
    token = encrypt_secret("hello", key=k1)
    with pytest.raises(CryptoError):
        decrypt_secret(token, key=k2)


def test_encrypt_uses_env_when_key_omitted(monkeypatch: pytest.MonkeyPatch) -> None:
    k = Fernet.generate_key().decode("ascii")
    monkeypatch.setenv("ENCRYPTION_KEY", k)
    token = encrypt_secret("x")
    assert decrypt_secret(token, key=k) == "x"
    assert decrypt_secret(token) == "x"


def test_encrypt_missing_env_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
    with pytest.raises(CryptoError, match="ENCRYPTION_KEY"):
        encrypt_secret("x")
