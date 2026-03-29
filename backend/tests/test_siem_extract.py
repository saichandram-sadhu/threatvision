"""SIEM IOC extraction."""

from __future__ import annotations

from app.services.siem.extract_iocs import extract_ioc_strings


def test_extract_wazuh_like_fields() -> None:
    payload = {
        "data": {"srcip": "198.51.100.10", "dstip": "192.0.2.1"},
        "full_log": "contact evil.example from 10.0.0.5",
    }
    out = extract_ioc_strings(payload)
    assert "198.51.100.10" in out
    assert "192.0.2.1" in out
    assert "evil.example" in out


def test_extract_respects_ioc_paths() -> None:
    payload = {
        "data": {"srcip": "1.1.1.1", "noise": "hello"},
        "_threatvision": {"iocPaths": ["data.noise"]},
    }
    out = extract_ioc_strings(payload)
    assert "1.1.1.1" in out
    assert "hello" not in out


def test_extract_hash_and_url() -> None:
    h = "a" * 32
    payload = {"ioc": h, "u": "https://phish.example/path"}
    out = extract_ioc_strings(payload)
    assert h in out
    assert "https://phish.example/path" in out
