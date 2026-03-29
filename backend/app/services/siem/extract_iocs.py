"""Extract IOC strings from SIEM JSON (lite dot paths + heuristic scan)."""

from __future__ import annotations

import ipaddress
import re
from typing import Any

from app.services.ioc.classify import normalize_ioc_value

_TV = "_threatvision"
_MAX_IOCS = 20
_MAX_STRING_LEN = 2048

_IPV4_RE = re.compile(
    r"^(?:(?:25[0-5]|2[0-4]\d|[01]?\d{1,2})\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d{1,2})$"
)
_DOMAIN_RE = re.compile(
    r"^(?!-)(?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,63}\.?$"
)
_URL_RE = re.compile(r"^https?://", re.I)
_MD5_RE = re.compile(r"^[a-fA-F0-9]{32}$")
_SHA1_RE = re.compile(r"^[a-fA-F0-9]{40}$")
_SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")
_SUBIP = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d{1,2})\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d{1,2})\b"
)
_SUBDOM = re.compile(
    r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}\b"
)
_SUBURL = re.compile(r"https?://[^\s<>\"']+", re.I)


def _looks_like_ioc_token(s: str) -> bool:
    s = normalize_ioc_value(s)
    if not s or len(s) > _MAX_STRING_LEN:
        return False
    token = s.split()[0] if s.split() else s
    if _MD5_RE.match(token) or _SHA1_RE.match(token) or _SHA256_RE.match(token):
        return True
    if _IPV4_RE.match(token):
        return True
    try:
        ipaddress.ip_address(token)
        return True
    except ValueError:
        pass
    if _URL_RE.match(s):
        return True
    if "/" not in token and _DOMAIN_RE.match(token) and "." in token and len(token) >= 4:
        return True
    return False


def _tokens_from_free_text(s: str, bucket: list[str]) -> None:
    """Pull IPv4, domains, and URLs out of long / composite strings (e.g. Wazuh ``full_log``)."""
    for m in _SUBIP.finditer(s):
        t = normalize_ioc_value(m.group(0))
        if _looks_like_ioc_token(t):
            bucket.append(t)
    for m in _SUBDOM.finditer(s):
        t = normalize_ioc_value(m.group(0))
        if _looks_like_ioc_token(t):
            bucket.append(t)
    for m in _SUBURL.finditer(s):
        t = normalize_ioc_value(m.group(0))
        if _looks_like_ioc_token(t):
            bucket.append(t)


def _get_by_path(obj: Any, dotted: str) -> Any:
    cur: Any = obj
    for part in dotted.split("."):
        if part == "":
            return None
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def _walk_strings(obj: Any, out: list[str], depth: int = 0) -> None:
    if depth > 30:
        return
    if isinstance(obj, str):
        if _looks_like_ioc_token(obj):
            out.append(normalize_ioc_value(obj))
        elif len(obj) > 20 or " " in obj or "\n" in obj:
            _tokens_from_free_text(obj, out)
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == _TV:
                continue
            _walk_strings(v, out, depth + 1)
        return
    if isinstance(obj, list):
        for item in obj[:500]:
            _walk_strings(item, out, depth + 1)


def extract_ioc_strings(payload: dict[str, Any]) -> list[str]:
    """
    Merge explicit dot-paths under ``_threatvision.iocPaths`` with a bounded recursive scan.
    Deduplicates while preserving order.
    """
    found: list[str] = []
    tv = payload.get(_TV)
    if isinstance(tv, dict):
        paths = tv.get("iocPaths") or tv.get("ioc_paths")
        if isinstance(paths, list):
            for p in paths:
                if not isinstance(p, str):
                    continue
                val = _get_by_path(payload, p.strip())
                if isinstance(val, str) and _looks_like_ioc_token(val):
                    found.append(normalize_ioc_value(val))
                elif isinstance(val, list):
                    for item in val[:50]:
                        if isinstance(item, str) and _looks_like_ioc_token(item):
                            found.append(normalize_ioc_value(item))

    scanned: list[str] = []
    _walk_strings(payload, scanned)

    for s in scanned:
        if s not in found:
            found.append(s)

    seen: set[str] = set()
    uniq: list[str] = []
    for s in found:
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        uniq.append(s)
        if len(uniq) >= _MAX_IOCS:
            break
    return uniq
