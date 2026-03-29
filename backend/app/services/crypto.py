"""Encrypt integration secrets at rest (Fernet — spec §2)."""

from __future__ import annotations

import os
from typing import Final

from cryptography.fernet import Fernet, InvalidToken

_ENV_KEY: Final[str] = "ENCRYPTION_KEY"


class CryptoError(Exception):
    """Invalid ciphertext, wrong key, or missing configuration."""


def _fernet_from_key(key: str | bytes) -> Fernet:
    if isinstance(key, str):
        key_b = key.encode("utf-8")
    else:
        key_b = key
    return Fernet(key_b)


def encryption_key_from_env() -> str:
    raw = os.environ.get(_ENV_KEY)
    if not raw or not raw.strip():
        raise CryptoError(f"Missing environment variable {_ENV_KEY}")
    return raw.strip()


def encrypt_secret(plain: str, *, key: str | bytes | None = None) -> str:
    """Return URL-safe base64 ciphertext string (Fernet token)."""
    k = key if key is not None else encryption_key_from_env()
    f = _fernet_from_key(k)
    return f.encrypt(plain.encode("utf-8")).decode("ascii")


def decrypt_secret(token: str, *, key: str | bytes | None = None) -> str:
    """Decrypt a Fernet token produced by encrypt_secret."""
    k = key if key is not None else encryption_key_from_env()
    f = _fernet_from_key(k)
    try:
        return f.decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken as e:
        raise CryptoError("Decryption failed (invalid token or wrong key)") from e
