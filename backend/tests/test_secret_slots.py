"""Vendor secret JSON key normalization."""

from __future__ import annotations

from app.services.integrations.secret_slots import canonical_secret_slot, normalize_secrets_dict
from app.services.ioc.integration_snapshot import parse_source_toggles


def test_canonical_virustotal_variants() -> None:
    assert canonical_secret_slot("virustotal") == "virustotal"
    assert canonical_secret_slot("VirusTotal") == "virustotal"
    assert canonical_secret_slot(" vt ") == "virustotal"
    assert canonical_secret_slot("\ufeffvirustotal") == "virustotal"


def test_normalize_merges_aliases() -> None:
    d = normalize_secrets_dict({"VT": "k1", "virustotal": "k2"})
    assert d == {"virustotal": "k2"}


def test_parse_source_toggles_json_string() -> None:
    assert parse_source_toggles('{"otx": false}') == {"otx": False}
    assert parse_source_toggles("{}") == {}
