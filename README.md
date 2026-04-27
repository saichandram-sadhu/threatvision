# ThreatVision

Full-stack cybersecurity IOC analysis and threat intelligence platform (MISP-centric, VirusTotal-style per-vendor transparency).

**Developed by:** Saichandram Sadhu

## Monorepo layout

| Path | Stack | Deploy target |
|------|--------|----------------|
| `frontend/` | Next.js 14 (App Router), TypeScript, Tailwind, Framer Motion, R3F, GSAP, NextAuth | Vercel |
| `backend/` | FastAPI, asyncpg, Pydantic v2 | Railway |
| `docs/` | Specs, plans, integration guides | — |

## Local development

### Prerequisites

- **Node.js** 20+ and npm  
- **Python** 3.11+  
- **PostgreSQL** 15+ — easiest: **Docker Desktop** + `threatvision/docker-compose.yml` (Postgres on host port **55432**)

### Quick setup (Windows)

1. Put your bootstrap email in **`threatvision/.env.example`** as `SUPERADMIN_EMAIL=...` (then scripts copy it into `backend/.env`).
2. Start **Docker Desktop**, then from **`threatvision/`**:

```powershell
.\scripts\setup_local.ps1
```

This generates **`backend/.env`** + **`frontend/.env.local`**, runs **`docker compose up -d`**, and applies all SQL migrations.

**One command (Docker + DB + API user + optional servers):** after `.env` exists, run:

```powershell
.\backend\.venv\Scripts\python.exe .\scripts\auto_everything.py
```

It registers **`SUPERADMIN_EMAIL`** from `backend/.env` and writes **`threatvision/.dev_login_credentials.txt`** (gitignored) with the random password for **`http://127.0.0.1:3001/login`**. Re-run if you need a fresh DB; if the user already exists you’ll get HTTP 409 and the file explains that.

### Supabase (hosted Postgres)

Solid fit for ThreatVision: **managed Postgres**, backups, and you keep **NextAuth + FastAPI** as-is (no need to switch to Supabase Auth unless you want to later).

1. In [Supabase](https://supabase.com) → **Project Settings → Database**, copy the **URI** (direct connection, port **5432** — not the pooler on 6543 for migrations).
2. Set in **`backend/.env`**:
   - `DATABASE_URL=postgresql://postgres.[ref]:YOUR_PASSWORD@db.[ref].supabase.co:5432/postgres`
   - `DATABASE_SSL=require`
3. From **`threatvision/backend`**, run migrations once:  
   `.\.venv\Scripts\python.exe .\scripts\apply_migrations.py`  
4. Register your **`SUPERADMIN_EMAIL`** via **`POST /auth/register`** or the app’s register page, or use **`scripts/auto_everything.py`** against that URL.

Use **direct `db.*.supabase.co:5432`** for `asyncpg` and migrations. The transaction pooler (`:6543`) can conflict with prepared statements; if you must use pooler, prefer **session mode** and test login + IOC flows end-to-end.

If you use your own Postgres instead of Docker, edit **`backend/.env`** `DATABASE_URL` accordingly, then run only:

```powershell
.\backend\.venv\Scripts\python.exe .\scripts\bootstrap_env.py
.\backend\.venv\Scripts\python.exe .\backend\scripts\apply_migrations.py
```

API default in generated `frontend/.env.local` is **`http://127.0.0.1:8001`** (change if you use port 8000). Start API from **`backend/`** with `uvicorn app.main:app --reload --host 127.0.0.1 --port 8001`.

### Environment variables

| Variable | Where | Purpose |
|----------|--------|---------|
| `DATABASE_URL` | Backend | `postgresql://user:pass@host:5432/threatvision` (Supabase: direct `db.*.supabase.co:5432`) |
| `DATABASE_SSL` | Backend | Omit for local Docker. Set `require` for Supabase / TLS-only hosts |
| `ENCRYPTION_KEY` | Backend | Fernet key (URL-safe base64, 32-byte) |
| `INTERNAL_JWT_SECRET` | Backend | HS256 secret for BFF ↔ API short-lived JWT |
| `INTERNAL_JWT_EXPIRE_MINUTES` | Backend | Internal JWT TTL (default 5) |
| `BFF_SERVICE_KEY` | Backend + Next server | Shared secret for internal auth exchange only |
| `API_KEY_PEPPER` | Backend | Server secret for HMAC-SHA256 of user API keys (lookup + verify) |
| `SUPERADMIN_EMAIL` | Backend | Login email (lowercased) that may become the single `SUPERADMIN` when no other superadmin exists |
| `CORS_ORIGINS` | Backend | Comma-separated browser origins allowed for CORS (include your Vercel URL in production) |
| `MAX_REQUEST_BODY_BYTES` | Backend | Max `Content-Length` for `POST`/`PUT`/`PATCH` (default 8 MiB; min 64 KiB, max 100 MiB) |
| `GEMINI_API_KEY` | Backend | Executive summary in PDF (optional) |
| `NEXTAUTH_SECRET` | Frontend | NextAuth session encryption |
| `NEXTAUTH_URL` | Frontend | Canonical app URL (e.g. `https://app.example.com`) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Frontend | Google OAuth (optional) |
| `GITHUB_ID` / `GITHUB_SECRET` | Frontend | GitHub OAuth (optional) |
| `NEXT_PUBLIC_APP_URL` | Frontend | Browser-facing app URL |
| `BACKEND_URL` | Frontend (server) | FastAPI origin for BFF proxy `/api/threatvision/*` |
| `PLATFORM_MISP_URL` | Backend (optional) | Docker MISP on host: often `https://127.0.0.1` (same as browser `https://localhost`) |
| `PLATFORM_MISP_API_KEY` | Backend (optional) | MISP **Automation → List Auth keys** (used by `set_platform_misp_from_env.py`) |
| `MISP_TLS_VERIFY` | Backend | Default `true`. Set `false` for **local Docker MISP** with a self-signed cert |
| `PLATFORM_MISP_URL` / `PLATFORM_MISP_API_KEY` | Backend | Also read by **Pydantic Settings** as `platform_misp_*` — used if `platform_settings` decrypt fails; `set_platform_misp_from_env.py` writes these to `.env` |

### Docker MISP on the same machine

ThreatVision talks to MISP **from FastAPI** (server-side `httpx`), not from the browser — so you usually use the **host URL** your MISP container publishes.

1. Confirm the container is listening (example: `misp-misp-core-1` with **80** and **443** on the host). If the UI is **`https://localhost`**, set **`PLATFORM_MISP_URL=https://127.0.0.1`** and **`MISP_TLS_VERIFY=false`** (self-signed).
2. In MISP: **Automation** → **List Auth keys** → create/copy an authkey with the permissions you need.
3. In **`backend/.env`** set `PLATFORM_MISP_URL` and `PLATFORM_MISP_API_KEY`.
4. Run once (or it runs from `scripts/setup_local.ps1` after migrations):

```powershell
cd threatvision\backend
.\.venv\Scripts\python.exe .\scripts\set_platform_misp_from_env.py
```

The script picks a working API key in order: **`PLATFORM_MISP_API_KEY`** in `.env` → existing ciphertext in **ThreatVision Postgres** → legacy **`users.authkey`** in MISP MySQL → **`docker exec … cake user change_authkey`** on **`misp-misp-core-1`** (MISP 2.5+ stores keys in **`auth_keys`**, so Cake is often required the first time). It does **not** rotate the key on later runs if the saved key still pings.

That writes **platform MISP fallback** in Postgres (used for every user who has not saved their own MISP under **Settings**). Superadmin can also view/edit the same values under **Admin → Platform MISP fallback**.

### MISP API (internal JWT)

All routes expect `Authorization: Bearer <internal JWT>` from the BFF exchange.

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/settings/misp/test` | Ping MISP (`servers/getVersion`); body may omit `base_url` / `api_key` to use saved user or platform fallback |
| `PUT` | `/settings/misp` | Save user MISP URL + API key (Fernet-encrypted in DB) |
| `GET` | `/misp/explorer` | Feeds, servers, taxonomies, stats; **30s** per-user JSON cache in `misp_explorer_cache` |
| `POST` | `/ioc/analyze` | Classify IOC, query MISP (`attributes/restSearch`), return **full vendor grid** (MISP + placeholders); applies **daily rate limit**; logs `activity_log` |

`POST /ioc/analyze` body: `{ "ioc": "<string>" }` — requires internal JWT. Response matches spec §4.2 (`ioc`, `aggregate`, `sources[]`). IOC strings are **sanitized** (control characters removed) before analysis.

### Browser → FastAPI (M11)

After email/password sign-in, the browser calls **`/api/threatvision/<fastapi-path>`** (same origin). The Next.js route exchanges an internal JWT (`BFF_SERVICE_KEY` + `POST /internal/auth/exchange`) and forwards to **`BACKEND_URL`**. OAuth (Google/GitHub) is optional; BFF calls require a credentials session (Postgres user UUID).

### Run two processes

**Terminal 1 — API**

Set `INTERNAL_JWT_SECRET`, `BFF_SERVICE_KEY`, and `API_KEY_PEPPER` in `.env` (see `.env.example`) before starting the API.

```powershell
cd threatvision\backend
.\.venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Web**

```powershell
cd threatvision\frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Production deployment (M17)

| Target | Artifact | Notes |
|--------|----------|--------|
| **Vercel** | `frontend/` | Set all frontend env vars from the table above. `BACKEND_URL` must point at your public Railway (or other) API URL. `BFF_SERVICE_KEY` must match the backend. |
| **Railway** | `backend/Dockerfile` + `backend/railway.toml` | Create a service with root directory **`backend`**. Set `DATABASE_URL`, `INTERNAL_JWT_SECRET`, `BFF_SERVICE_KEY`, `API_KEY_PEPPER`, `SUPERADMIN_EMAIL`, `ENCRYPTION_KEY`, and **`CORS_ORIGINS`** to your Vercel origin(s). Optional: `GEMINI_API_KEY`. The image includes WeasyPrint system libraries. |

After deploy, confirm `GET https://<api>/health` returns `{"status":"ok"}` and that the browser app can reach the API through the Next.js BFF (same-origin `/api/threatvision/...`).

## Database migrations

SQL lives in `backend/app/db/migrations/`. After `backend/.env` exists with `DATABASE_URL`, apply everything in order:

```powershell
cd threatvision
.\backend\.venv\Scripts\python.exe .\backend\scripts\apply_migrations.py
```

Or use **`scripts/setup_local.ps1`** (includes Docker Postgres + this step).

**Opt-in integration tests (destructive):** reset the **`public`** schema on the target database.

```powershell
$env:TEST_DATABASE_URL = "postgresql://user:pass@localhost:5432/threatvision_test"
$env:RUN_DB_MIGRATION_TESTS = "1"
cd threatvision\backend
.\.venv\Scripts\pytest tests\test_migrations_apply.py::test_migrations_apply_to_database -v
.\.venv\Scripts\pytest tests\test_m3_integration.py::test_auth_superadmin_and_rate_limit_flow -v
```

## Testing & QA (M18)

**Backend:** from `threatvision/backend` with dev dependencies installed:

```powershell
.\.venv\Scripts\pytest -q
```

Coverage highlights: IOC **classify** / **consensus**, **rate_limit** (fake pool), **MISP explorer parsers** (JSON fixtures under `tests/fixtures/misp/`), **OTX enricher** (respx HTTP mock).

**Frontend (Playwright):** from `threatvision/frontend`:

```powershell
npm install
npx playwright install chromium
npm run test:e2e
```

By default, smoke tests hit **login**, **/analyze → /login** (NextAuth middleware), and **about** while `npm run dev` starts (or reuses a running server). Set **`NEXTAUTH_SECRET`** for local runs. To also assert the **vendor breakdown** after a real analyze, set **`E2E_EMAIL`** and **`E2E_PASSWORD`** for a credentials user, run the **API** and **Next** with valid **`BACKEND_URL`** / **`BFF_SERVICE_KEY`**, then run `npm run test:e2e`.

**Manual checklist** (MISP Docker, feed attribution, etc.): [docs/qa/M18-manual-checklist.md](docs/qa/M18-manual-checklist.md).

## Documentation

- [Design spec](docs/specs/2026-03-29-threatvision-design.md)
- [Implementation plan](docs/plans/2026-03-29-threatvision-implementation-plan.md)

## License

See repository license (to be added).
