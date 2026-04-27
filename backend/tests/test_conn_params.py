"""TLS helper for hosted Postgres."""

from __future__ import annotations

import pytest

from app.db.conn_params import ssl_connect_arg


@pytest.mark.parametrize(
    ("raw", "expect"),
    [
        (None, None),
        ("", None),
        (" \t ", None),
        ("0", None),
        ("false", None),
        ("disable", None),
        ("1", "require"),
        ("true", "require"),
        ("yes", "require"),
        ("require", "require"),
        ("REQUIRE", "require"),
    ],
)
def test_ssl_connect_arg(raw: str | None, expect: str | None) -> None:
    assert ssl_connect_arg(raw) == expect
