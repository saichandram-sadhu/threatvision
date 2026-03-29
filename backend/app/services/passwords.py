"""Argon2 password hashing for credential auth."""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, password_hash: str) -> bool:
    try:
        _hasher.verify(password_hash, plain)
        if _hasher.check_needs_rehash(password_hash):
            # Future: persist upgraded hash on successful login
            pass
        return True
    except VerifyMismatchError:
        return False
