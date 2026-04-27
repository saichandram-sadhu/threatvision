# ThreatVision Backend

FastAPI service: PostgreSQL (asyncpg), MISP, enrichers, reports, webhooks.

## Setup

```bash
cd threatvision/backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Run (after app exists)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

See root `../README.md` for environment variables.

## Docker / Railway

Build from this directory (the Dockerfile expects `pyproject.toml`, `README.md`, and `app/` here):

```bash
docker build -t threatvision-api .
docker run --rm -p 8000:8000 --env-file .env threatvision-api
```

Railway: set the service **root** to `backend` (in a monorepo), use **`railway.toml`**, and configure **`PORT`** via the platform (the default start command uses `$PORT`). Set **`CORS_ORIGINS`** to your deployed Next.js origin.

## PDF reports (WeasyPrint)

`POST /reports/pdf` renders HTML via **Jinja2** and converts with **WeasyPrint**. On Linux servers (e.g. Railway/Docker), install Cairo, Pango, and GDK-Pixbuf (e.g. Debian/Ubuntu: `apt install libcairo2 libpango-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info`). On Windows, WeasyPrint may require extra GTK/runtime setup; if the engine fails to load, the API returns **503** with `pdf_engine_unavailable`.

Optional **`GEMINI_API_KEY`**: enables the AI executive summary in the PDF; if missing or the API errors, a **placeholder** summary is used and vendor tables are unchanged.

## Superadmin admin API (M10)

Routes under **`/admin`** require a **short-lived internal JWT** whose `role` claim is **`SUPERADMIN`**, and the caller’s **database user** must also be **`SUPERADMIN`** with **`email`** equal to **`SUPERADMIN_EMAIL`** (env) — same bootstrap rule as login promotion.

- **`GET /admin/users`** — list users (limit 500).
- **`PATCH /admin/users/{user_id}`** — `dailyLimit`, `unlimited`, `banned` (omit fields to leave unchanged; cannot ban yourself).
- **`POST /admin/users/{user_id}/regenerate-api-key`** — new API key returned **once** in JSON.
- **`GET /admin/platform/misp`** — platform MISP fallback URL + whether an encrypted API key is stored.
- **`PUT /admin/platform/misp`** — set/clear `misp_fallback_url` and/or `misp_fallback_api_key` (Fernet-encrypted at rest; omit a field to leave it unchanged; empty string clears URL or key).

## SIEM webhooks (M9)

`POST /api/webhook/siem/{path_key}` (or `/api/webhook/siem` + `X-Tv-Path-Key`) accepts JSON alerts, extracts IOCs, and runs the normal analyze pipeline. See `../docs/integrations/siem-webhooks.md` for auth (path-only, bearer `X-Tv-Webhook-Secret`, optional HMAC + timestamp), Wazuh-oriented examples, and how to provision `webhook_secrets` + migration `005_webhook_path_key.sql`.
