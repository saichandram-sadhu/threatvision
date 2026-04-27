"""Normalize vendor secret JSON keys to catalog slot ids (e.g. VirusTotal → virustotal)."""

from __future__ import annotations

# Alphanumeric-normalized alias → canonical ``user_integration_settings.secrets`` key
_SLOT_BY_NORMALIZED: dict[str, str] = {
    "virustotal": "virustotal",
    "vt": "virustotal",
    "abuseipdb": "abuseipdb",
    "abuseip": "abuseipdb",
    "shodan": "shodan",
    "urlscan": "urlscan",
    "urlscanio": "urlscan",
    "safebrowsing": "safebrowsing",
    "greynoise": "greynoise",
    "greynoisecommunity": "greynoise",
    "ibm": "ibm_xforce",
    "ibmxforce": "ibm_xforce",
    "xforce": "ibm_xforce",
    "otx": "otx",
    "alienvault": "otx",
    "alienvaultotx": "otx",
}


def _strip_key(raw: str) -> str:
    return raw.strip().strip("\ufeff").strip()


def _normalized_alnum(s: str) -> str:
    return "".join(c for c in s.lower() if c.isalnum())


def canonical_secret_slot(raw_key: str) -> str:
    """Map UI / legacy / typo keys to the enricher snapshot key."""
    k0 = _strip_key(raw_key)
    if not k0:
        return ""
    nk = _normalized_alnum(k0)
    if nk in _SLOT_BY_NORMALIZED:
        return _SLOT_BY_NORMALIZED[nk]
    return k0.lower().replace("-", "_")


def normalize_secrets_dict(secrets: dict[str, str]) -> dict[str, str]:
    """Merge values onto canonical keys (last wins)."""
    out: dict[str, str] = {}
    for k, v in secrets.items():
        if v is None:
            continue
        val = str(v).strip().strip("\ufeff").strip()
        if not val:
            continue
        ck = canonical_secret_slot(k)
        if not ck:
            continue
        out[ck] = val
    return out
