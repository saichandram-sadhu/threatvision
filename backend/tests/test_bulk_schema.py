"""Bulk API request validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.bulk import BulkCreateIn


def test_bulk_rejects_over_500_iocs() -> None:
    with pytest.raises(ValidationError):
        BulkCreateIn(iocs=[f"x{i}" for i in range(501)])


def test_bulk_rejects_all_empty_after_strip() -> None:
    with pytest.raises(ValidationError):
        BulkCreateIn(iocs=["  ", "\t"])


def test_bulk_accepts_500() -> None:
    b = BulkCreateIn(iocs=[f"{i}.example.com" for i in range(500)])
    assert len(b.iocs) == 500
