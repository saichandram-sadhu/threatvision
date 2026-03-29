# SIEM webhooks (ThreatVision M9)

ThreatVision accepts **generic JSON** alerts from SIEM tools (including Wazuh) at:

- `POST /api/webhook/siem/{path_key}` — recommended (path identifies your endpoint)
- `POST /api/webhook/siem` with header **`X-Tv-Path-Key: {path_key}`** — same behavior

`path_key` is an **unguessable slug** stored in `webhook_secrets.path_key` for your user (see provisioning below).

## Authentication modes

| Mode | `secret_hash` in DB | `hmac_optional` | Requirements |
|------|---------------------|-----------------|--------------|
| Path-only | `NULL` | `false` | Valid `path_key` only (URL secrecy). |
| Bearer | set (HMAC hash) | `false` | Header **`X-Tv-Webhook-Secret`** with the plaintext secret. Hash uses the same scheme as API keys (`HMAC-SHA256(pepper, secret)` with server `API_KEY_PEPPER`). |
| HMAC | set | `true` | **`X-Tv-Webhook-Secret`** (same plaintext as above) **plus** **`X-Tv-Timestamp`** (Unix seconds) and **`X-Tv-Signature`** (hex SHA-256 HMAC of `{timestamp}.{raw_body}` using the plaintext secret as key). Timestamp must be within **300 seconds** of server time. |

## IOC extraction

1. **Optional explicit paths** — include a `_threatvision` object in the JSON body:

```json
{
  "agent": { "ip": "192.0.2.10" },
  "data": { "srcip": "198.51.100.2", "dstip": "10.0.0.1" },
  "_threatvision": {
    "iocPaths": ["data.srcip", "data.dstip", "agent.ip"]
  }
}
```

2. **Heuristic scan** — all string values in the JSON are scanned for IPv4/IPv6, URLs, domains, and hashes (MD5/SHA1/SHA256). Up to **20** unique candidates are analyzed, in order.

## Example: Wazuh-style payload (generic)

```json
{
  "timestamp": "2026-03-29T12:00:00Z",
  "rule": { "id": "100001", "description": "Suspicious outbound" },
  "data": {
    "srcip": "198.51.100.88",
    "dstip": "203.0.113.50",
    "url": "https://evil.example/malware"
  },
  "full_log": "connection to bad-domain.example on port 443"
}
```

Point your integration at:

`POST https://<your-api-host>/api/webhook/siem/<path_key>`

## Response shape

```json
{
  "accepted": true,
  "iocCount": 3,
  "analyzed": 3,
  "results": [
    {
      "ioc": "198.51.100.88",
      "normalized": "198.51.100.88",
      "type": "ip",
      "verdict": "MALICIOUS",
      "confidence": 82,
      "error": null
    }
  ],
  "message": null
}
```

If the user’s **daily rate limit** is exceeded mid-batch, remaining IOCs are skipped and `message` explains partial processing.

## Provisioning `webhook_secrets` (v1)

Until an admin UI exists, insert a row per user (PostgreSQL), e.g.:

```sql
-- path_key: long random slug (example)
-- secret_hash: HMAC-SHA256(API_KEY_PEPPER, plaintext_secret) as hex, same as users.api_key_hash
-- Or NULL secret_hash for path-only mode.

INSERT INTO webhook_secrets (user_id, secret_hash, hmac_optional, path_key)
VALUES (
  '<user-uuid>',
  NULL,
  false,
  'replace-with-long-random-slug'
);
```

Generate the **hash** for a chosen plaintext secret using the backend (same pepper as in `.env`):

```bash
cd threatvision/backend && python -c "
from app.config import get_settings
from app.auth.api_key import compute_api_key_hash
s = get_settings()
print(compute_api_key_hash('YOUR_PLAINTEXT_SECRET', s.api_key_pepper))
"
```

Use the printed hex as `secret_hash` when you require **`X-Tv-Webhook-Secret: YOUR_PLAINTEXT_SECRET`**.

## HMAC signature (when `hmac_optional = true`)

- `T =` Unix time (seconds), header `X-Tv-Timestamp: T`
- `M =` raw request body bytes (exactly as sent)
- `message = f"{T}.".encode('utf-8') + M`
- `signature = HMAC_SHA256(key=plaintext_secret, message).hexdigest()`
- Header `X-Tv-Signature: <hex digest>` (case-insensitive compare)

## Security notes

- Treat **`path_key` like a password** if you use path-only mode.
- Prefer **bearer** or **HMAC** for untrusted networks.
- Use HTTPS only in production.
