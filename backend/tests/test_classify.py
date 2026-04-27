"""IOC type detection."""

from __future__ import annotations

from app.services.ioc.classify import classify_ioc, normalize_ioc_value, search_value_for_misp


def test_classify_ipv4() -> None:
    t, n = classify_ioc("8.8.8.8")
    assert t == "ip"
    assert n == "8.8.8.8"


def test_classify_md5() -> None:
    t, n = classify_ioc("5d41402abc4b2a76b9719d911017c592")
    assert t == "hash"
    assert n == "5d41402abc4b2a76b9719d911017c592"


def test_classify_sha256() -> None:
    h = "a" * 64
    t, n = classify_ioc(h)
    assert t == "hash"


def test_classify_url() -> None:
    t, n = classify_ioc("https://evil.example/phish")
    assert t == "url"


def test_classify_domain() -> None:
    t, n = classify_ioc("example.com")
    assert t == "domain"
    assert n == "example.com"


def test_search_value_email_header_extracts_ip() -> None:
    body = "Received: from x\nReceived: from [192.168.1.1]"
    t, n = classify_ioc(body)
    assert t == "email_header"
    assert search_value_for_misp(t, n) == "192.168.1.1"


def test_classify_ipv6() -> None:
    t, n = classify_ioc("2001:db8::1")
    assert t == "ip"
    assert ":" in n


def test_classify_sha1() -> None:
    h = "a" * 40
    t, n = classify_ioc(h)
    assert t == "hash"
    assert len(n) == 40


def test_normalize_strips_wrapping_quotes() -> None:
    assert normalize_ioc_value('"evil.example"') == "evil.example"
    assert normalize_ioc_value("'8.8.8.8'") == "8.8.8.8"


def test_classify_domain_with_trailing_dot() -> None:
    t, n = classify_ioc("Example.COM.")
    assert t == "domain"
    assert n == "example.com"
