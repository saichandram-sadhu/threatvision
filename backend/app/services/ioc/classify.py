"""Detect IOC type from a single string (spec §4.2)."""

from __future__ import annotations

import ipaddress
import re
from typing import Literal

IocType = Literal["ip", "hash", "domain", "url", "email_header"]

_IPV4_RE = re.compile(
    r"^(?:(?:25[0-5]|2[0-4]\d|[01]?\d{1,2})\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d{1,2})$"
)
# Loose domain (no scheme)
_DOMAIN_RE = re.compile(
    r"^(?!-)(?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,63}\.?$"
)
_URL_RE = re.compile(r"^https?://", re.I)
_MD5_RE = re.compile(r"^[a-fA-F0-9]{32}$")
_SHA1_RE = re.compile(r"^[a-fA-F0-9]{40}$")
_SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")
# Email header heuristics
_HEADER_MARKERS = re.compile(
    r"(?mi)^(Received:|From:|Return-Path:|DKIM-Signature:|Authentication-Results:)",
)


def _strip_wrapping_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"":
        return s[1:-1].strip()
    return s


def normalize_ioc_value(raw: str) -> str:
    return _strip_wrapping_quotes(raw).strip()


def classify_ioc(raw: str) -> tuple[IocType, str]:
    """
    Return ``(ioc_type, normalized_value)``.
    Order: hash → ip → url → email_header → domain.
    """
    s = normalize_ioc_value(raw)
    if not s:
        return "domain", s

    token = s.split()[0] if s.split() else s

    if _MD5_RE.match(token) or _SHA1_RE.match(token) or _SHA256_RE.match(token):
        return "hash", token.lower()

    if _IPV4_RE.match(token):
        return "ip", token

    try:
        ipaddress.ip_address(token)
        return "ip", token
    except ValueError:
        pass

    if _URL_RE.match(s):
        return "url", s

    if _HEADER_MARKERS.search(s) or (s.count("\n") >= 2 and "@" in s and ":" in s):
        return "email_header", s

    if "/" not in token and _DOMAIN_RE.match(token):
        return "domain", token.rstrip(".").lower()

    if "@" in token and "." in token and " " not in token:
        return "domain", token.split("@", 1)[-1].lower()

    return "domain", token.lower()


def search_value_for_misp(ioc_type: IocType, normalized: str) -> str:
    """Value sent to MISP ``restSearch`` (trim email bodies to a useful token)."""
    if ioc_type == "email_header":
        m = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", normalized)
        if m:
            return m.group(0)
        m2 = re.search(
            r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}\b",
            normalized,
        )
        if m2:
            return m2.group(0).lower()
        return normalized[:256].strip()
    return normalized
