# M18 — Manual QA checklist

Run against a stack where **FastAPI**, **Postgres**, **Next.js**, and (for MISP items) a **MISP 2.4.x** instance are configured and reachable.

## Explorer & MISP

- [ ] Sign in (email/password), open **Settings → MISP** or dashboard **MISP Health** widget.
- [ ] **Explorer** loads feeds, servers, taxonomies, and stats without persistent 502s.
- [ ] **Test connection** succeeds with saved URL + API key (or explicit test body).

## Single IOC + feed attribution

- [ ] **Analyze** an indicator known to exist in MISP (e.g. test attribute).
- [ ] **Vendor breakdown** lists sources in catalog order; MISP row shows plausible detail lines.
- [ ] Expand **MISP events** (if any): event table shows **Feed / source** column populated where your instance provides feed metadata (see spec §4.10.8).

## Webhooks & bulk (spot-check)

- [ ] Optional: send a sample payload to **`POST /api/webhook/siem/{path_key}`** and confirm JSON response lists analyzed IOCs.
- [ ] Optional: **Bulk** job completes and SSE progress reaches **complete** for a small list.

## PDF

- [ ] Optional: from bulk or analyze UI, request **PDF** export and confirm download opens (WeasyPrint available on API host).

## Security (production-shaped)

- [ ] Browser **Origin** is listed in backend **`CORS_ORIGINS`**; no unintended wildcard in production.
- [ ] Oversized **`POST`** bodies are rejected (**413**) when above **`MAX_REQUEST_BODY_BYTES`**.

Record environment (MISP version, ThreatVision commit) and any failures for follow-up.
