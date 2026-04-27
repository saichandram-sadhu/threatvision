"""IOC input sanitization (M17)."""

from app.services.ioc.sanitize import sanitize_ioc_input


def test_sanitize_strips_null_and_controls() -> None:
    assert sanitize_ioc_input("evil\x00.com") == "evil.com"
    assert sanitize_ioc_input("a\x1fb") == "ab"


def test_sanitize_collapses_whitespace() -> None:
    assert sanitize_ioc_input("  8.8.8.8  \n\t") == "8.8.8.8"


def test_sanitize_drops_format_chars() -> None:
    s = "test\u200bvalue"
    assert "\u200b" not in sanitize_ioc_input(s)


def test_sanitize_empty() -> None:
    assert sanitize_ioc_input("") == ""
    assert sanitize_ioc_input("\x00\x01\x02") == ""
