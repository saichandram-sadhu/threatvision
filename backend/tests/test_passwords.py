"""Argon2 password helpers."""

from __future__ import annotations

from app.services.passwords import hash_password, verify_password


def test_hash_and_verify() -> None:
    h = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", h)
    assert not verify_password("wrong", h)
