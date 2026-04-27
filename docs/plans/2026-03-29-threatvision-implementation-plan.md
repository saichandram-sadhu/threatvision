# ThreatVision Implementation Plan

> **For agentic workers:** Use **subagent-driven-development** or **executing-plans** to implement this plan task-by-task. Track progress with checkbox (`- [ ]`) steps.

**Goal:** Ship ThreatVision v1: Next.js 14 BFF + FastAPI + PostgreSQL IOC platform with per-vendor breakdown, MISP Instance Explorer, bulk SSE, PDF reports (Gemini summary), SIEM webhooks, and admin/superadmin controls—per [spec](../specs/2026-03-29-threatvision-design.md).

**Architecture:** Browser authenticates via **NextAuth** on Vercel. Next.js **server** calls **FastAPI** on Railway with a **short-lived internal JWT**. FastAPI owns persistence (asyncpg), **AES-256** integration secrets, **MISP + enrichers**, **Postgres rate limits**, **webhooks**, and **PDF** generation. **MISP Explorer** and **IOC analysis** share a **feed id → name** map from live MISP API responses.

**Tech Stack:** Next.js 14 App Router, TypeScript, Tailwind, Framer Motion, R3F/Three, GSAP; FastAPI, asyncpg, Pydantic v2; PostgreSQL; NextAuth (credentials + Google + GitHub); PyMISP or httpx for MISP REST; WeasyPrint *or* ReportLab for PDF; Google Gemini `gemini-1.5-flash` for executive summary.

---

## File structure (create as you go)

| Area | Path | Responsibility |
|------|------|----------------|
| Backend entry | `threatvision/backend/app/main.py` | FastAPI app, CORS, router include |
| Config | `threatvision/backend/app/config.py` | Env: `DATABASE_URL`, `ENCRYPTION_KEY`, `INTERNAL_JWT_SECRET`, `SUPERADMIN_EMAIL`, `GEMINI_API_KEY`, optional platform MISP fallback |
| DB | `threatvision/backend/app/db/pool.py`, `app/db/migrations/` | asyncpg pool; SQL migrations (numbered `.sql` or Alembic) |
| Models / schemas | `threatvision/backend/app/schemas/` | Pydantic request/response; `source_result.py` matches spec §4.2 |
| Auth | `threatvision/backend/app/auth/internal_jwt.py`, `api_key.py` | Verify internal JWT; hash/verify user API keys |
| Crypto | `threatvision/backend/app/services/crypto.py` | Fernet or AES-GCM with per-row IV |
| Users / settings | `threatvision/backend/app/routers/users.py`, `settings.py` | Profile, encrypted integration fields, toggles |
| MISP | `threatvision/backend/app/services/misp/client.py` | Resolved base URL + key; timeouts |
| MISP explorer | `threatvision/backend/app/services/misp/explorer.py` | Aggregates feeds, servers, taxonomies, stats |
| MISP IOC | `threatvision/backend/app/services/misp/ioc_search.py` | Search events/attributes; build `events[]` + **feed attribution** §4.10.8 |
| IOC pipeline | `threatvision/backend/app/services/ioc/classify.py`, `pipeline.py`, `consensus.py` | Type detection; parallel enrichers; aggregate verdict |
| Enrichers | `threatvision/backend/app/services/enrichers/*.py` | One module per catalog id (§4.4); shared protocol |
| Rate limit | `threatvision/backend/app/services/rate_limit.py` | Postgres counters, daily limit, superadmin override |
| Bulk | `threatvision/backend/app/routers/bulk.py`, `services/bulk/job.py` | Job rows, SSE stream |
| PDF | `threatvision/backend/app/services/reports/pdf.py`, `gemini.py` | Degraded summary on failure (spec §2) |
| Webhooks | `threatvision/backend/app/routers/webhooks.py` | SIEM + HMAC optional |
| Admin | `threatvision/backend/app/routers/admin.py` | Superadmin-only guards |
| Tests | `threatvision/backend/tests/` | pytest, httpx AsyncClient, DB fixtures |
| Frontend | `threatvision/frontend/` | Next.js app: `app/`, `components/`, `lib/` |
| BFF | `threatvision/frontend/app/api/backend/[...path]/route.ts` (or per-route) | Forward cookie session → internal JWT → FastAPI |
| UI centerpiece | `threatvision/frontend/components/ioc/VendorBreakdownTable.tsx` | Spec §4.1–4.9 |
| MISP UI | `threatvision/frontend/app/(app)/settings/misp/page.tsx`, `components/misp/MispExplorerPanel.tsx` | §4.10 |
| Dashboard | `threatvision/frontend/app/(app)/dashboard/page.tsx`, `components/dashboard/MispHealthWidget.tsx` | §4.10.6 |

---

## Milestone M0 — Monorepo scaffold & tooling

### Task M0.1: Repository layout

**Files:**
- Create: `threatvision/README.md`
- Create: `threatvision/.gitignore` (root: `node_modules`, `.env*`, `__pycache__`, `.venv`, `dist`)
- Create: `threatvision/frontend/package.json` (Next 14, React 18, TS, Tailwind, next-auth, framer-motion, @react-three/fiber, three, gsap)
- Create: `threatvision/backend/pyproject.toml` (fastapi, uvicorn, asyncpg, pydantic-settings, pyjwt, cryptography, httpx, pymisp *or* plain httpx)

- [ ] **Step 1:** Create `threatvision/` tree with empty `frontend/`, `backend/`, `docs/` as above.
- [ ] **Step 2:** `cd threatvision/frontend && npx create-next-app@14` (or manual) with **App Router**, **TypeScript**, **Tailwind**, `src/` optional—stay consistent.
- [ ] **Step 3:** `cd threatvision/backend && python -m venv .venv` and `pip install -e ".[dev]"` with pytest, ruff, httpx.
- [ ] **Step 4:** Add root README sections: local dev (Postgres URL, two terminals), env var table.
- [ ] **Step 5:** Commit: `chore: scaffold threatvision monorepo`

---

## Milestone M1 — PostgreSQL schema & encryption

### Task M1.1: Core tables migration

**Files:**
- Create: `threatvision/backend/app/db/migrations/001_initial.sql`
- Create: `threatvision/backend/tests/test_migrations_apply.py`

**Tables (minimal columns listed):**

- `users` — id (uuid), email unique, password_hash nullable (OAuth-only allowed), name, image_url, role enum (`USER`,`ADMIN`,`SUPERADMIN`), `api_key_hash`, `api_key_prefix`, `daily_limit` default 100, `unlimited` bool, `banned` bool, `created_at`
- `user_integration_settings` — user_id fk, jsonb `source_toggles`, encrypted blobs per provider or single jsonb ciphertext for keys
- `platform_settings` — singleton row for fallback MISP url+ciphertext key (ADMIN editable)
- `usage_counters` — user_id, date, request_count
- `ioc_jobs` — bulk job id, user_id, status, created_at
- `ioc_job_items` — job_id, ioc raw, type, aggregate jsonb, sources jsonb
- `activity_log` — user_id, ioc snippet, verdict, `flagged_by` jsonb (source ids), created_at
- `webhook_secrets` — user_id, secret_hash, hmac_optional bool

- [ ] **Step 1:** Write `001_initial.sql` with indexes on `users.email`, `usage_counters (user_id, date)`.
- [ ] **Step 2:** Write pytest that spins test DB (docker or local) and applies migration (psql or asyncpg execute file).
- [ ] **Step 3:** Run `pytest threatvision/backend/tests/test_migrations_apply.py -v` → PASS.
- [ ] **Step 4:** Commit: `feat(db): initial schema`

### Task M1.2: Encryption service

**Files:**
- Create: `threatvision/backend/app/services/crypto.py`
- Create: `threatvision/backend/tests/test_crypto_roundtrip.py`

- [ ] **Step 1:** Implement `encrypt_secret(plain: str) -> str` and `decrypt_secret(token: str) -> str` using **Fernet** (from `cryptography.fernet`) keyed by `ENCRYPTION_KEY` base64 urlsafe 32-byte.
- [ ] **Step 2:** Test roundtrip and wrong-key failure.
- [ ] **Step 3:** Commit: `feat(crypto): fernet envelope for integration secrets`

---

## Milestone M2 — FastAPI core, internal JWT, API key auth

### Task M2.1: App boot + health

**Files:**
- Create: `threatvision/backend/app/main.py`, `app/config.py`, `app/db/pool.py`

- [ ] **Step 1:** Load settings from env; create asyncpg pool on lifespan startup.
- [ ] **Step 2:** `GET /health` → `{"status":"ok"}`.
- [ ] **Step 3:** Run `uvicorn app.main:app --reload` and curl health.
- [ ] **Step 4:** Commit: `feat(api): fastapi skeleton and health`

### Task M2.2: Internal JWT issue/verify (for Next BFF)

**Files:**
- Create: `threatvision/backend/app/auth/internal_jwt.py`
- Create: `threatvision/backend/tests/test_internal_jwt.py`

- [ ] **Step 1:** `create_internal_token(sub=user_id, role=..., exp=5m)` with HS256 `INTERNAL_JWT_SECRET`.
- [ ] **Step 2:** Dependency `get_current_user_from_internal` for protected routes.
- [ ] **Step 3:** Expose `POST /internal/auth/exchange` **protected by** `X-Service-Key` header (shared secret `BFF_SERVICE_KEY`) that accepts Next-only calls: body `{ userId, role }` → returns JWT. *Refine in hardening milestone: map Next session server-side only.*
- [ ] **Step 4:** Tests for valid/invalid token and service key.
- [ ] **Step 5:** Commit: `feat(auth): internal jwt for bff`

### Task M2.3: User API key verification

**Files:**
- Create: `threatvision/backend/app/auth/api_key.py`
- Create: `threatvision/backend/tests/test_api_key_auth.py`

- [ ] **Step 1:** On registration / regenerate: generate UUID v4, store **hash** (argon2 or bcrypt of key), store **prefix** for display.
- [ ] **Step 2:** Dependency `get_user_from_api_key` for `/v1/...` programmatic routes.
- [ ] **Step 3:** Commit: `feat(auth): api key hashing and verification`

---

## Milestone M3 — Users, superadmin bootstrap, rate limits

### Task M3.1: Registration + login (email) in FastAPI

**Files:**
- Create: `threatvision/backend/app/routers/auth_password.py` (or `users.py`)
- Modify: `users` table usage

*Note: NextAuth may own OAuth; FastAPI must still store user row and accept password hashes for credential provider if you duplicate logic—prefer **NextAuth credentials callback** calling FastAPI `POST /auth/register` and `POST /auth/login` returning user id for session, OR use NextAuth adapter with Prisma on Postgres **same DB** as FastAPI. Pick **one DB** for users to avoid split brain.*

**Recommendation:** **Single Postgres**; NextAuth **Credentials** + **OAuth** with **custom adapter** via HTTP to FastAPI user endpoints, *or* use `@auth/pg-adapter` pattern with tables compatible with FastAPI. Document chosen approach in `threatvision/docs/auth.md`.

- [ ] **Step 1:** Implement `POST /auth/register` (email, password) — hash password with argon2.
- [ ] **Step 2:** Implement `POST /auth/login` — returns user id + role (no JWT to browser; Next handles session).
- [ ] **Step 3:** On first login if `email == SUPERADMIN_EMAIL`, set `role = SUPERADMIN` and enforce **no other** superadmin promotion paths.
- [ ] **Step 4:** Commit: `feat(users): register login and superadmin bootstrap`

### Task M3.2: Rate limiting (Postgres)

**Files:**
- Create: `threatvision/backend/app/services/rate_limit.py`
- Create: `threatvision/backend/tests/test_rate_limit.py`

- [ ] **Step 1:** `check_and_increment(user_id)` in transaction: if `unlimited` skip; else compare `usage_counters` for UTC date vs `daily_limit`.
- [ ] **Step 2:** Integrate dependency on `POST /ioc/analyze` and bulk endpoints.
- [ ] **Step 3:** Commit: `feat(rate-limit): postgres daily counters`

---

## Milestone M4 — MISP client, test connection, Explorer API

### Task M4.1: Resolved MISP config

**Files:**
- Create: `threatvision/backend/app/services/misp/client.py`
- Create: `threatvision/backend/app/services/misp/resolve.py`

- [ ] **Step 1:** `get_misp_config_for_user(user_id)` → (base_url, api_key_plain) from user ciphertext or platform fallback.
- [ ] **Step 2:** `httpx.AsyncClient` with timeout 30s, `Authorization: user_api_key` header per MISP.
- [ ] **Step 3:** Commit: `feat(misp): resolved client factory`

### Task M4.2: Test connection endpoint

**Files:**
- Create: `threatvision/backend/app/routers/misp_settings.py`

- [ ] **Step 1:** `POST /settings/misp/test` (internal JWT) — optional body url+key or use saved; call `GET /users/view/me` or `GET /servers/getVersion` MISP endpoint.
- [ ] **Step 2:** Return version string + ok flag.
- [ ] **Step 3:** Commit: `feat(misp): test connection`

### Task M4.3: MISP Explorer aggregation

**Files:**
- Create: `threatvision/backend/app/services/misp/explorer.py`
- Create: `threatvision/backend/app/schemas/misp_explorer.py`
- Create: `threatvision/backend/app/routers/misp_explorer.py`

- [ ] **Step 1:** Implement fetchers: `/feeds`, `/servers`, taxonomies list, statistics endpoints (map MISP 2.4.x REST paths; use PyMISP if faster).
- [ ] **Step 2:** Build response DTO: `feeds[]`, `servers[]`, `taxonomies[]`, `stats`, `syncIndicator` (derived), `fetchedAt`.
- [ ] **Step 3:** `GET /misp/explorer` (internal JWT) returns DTO; handle MISP errors with 502 + code.
- [ ] **Step 4:** Unit test with **recorded fixtures** (json files) for parser mapping.
- [ ] **Step 5:** Commit: `feat(misp): explorer aggregation endpoint`

### Task M4.4: Explorer snapshot caching (optional but recommended)

**Files:**
- Create: `threatvision/backend/app/services/misp/explorer_cache.py`

- [ ] **Step 1:** Cache last successful explorer JSON in Postgres (`user_id`, `payload jsonb`, `updated_at`) with TTL 30s read-through to avoid hammering MISP on dashboard poll.
- [ ] **Step 2:** Commit: `feat(misp): explorer snapshot cache`

---

## Milestone M5 — IOC classification, MISP search, feed attribution

### Task M5.1: IOC type detection

**Files:**
- Create: `threatvision/backend/app/services/ioc/classify.py`
- Create: `threatvision/backend/tests/test_classify.py`

- [ ] **Step 1:** Regex/heuristics for IPv4/6, MD5/SHA1/SHA256, domain, URL, email headers.
- [ ] **Step 2:** Commit: `feat(ioc): type classification`

### Task M5.2: MISP search + event assembly

**Files:**
- Create: `threatvision/backend/app/services/misp/ioc_search.py`
- Create: `threatvision/backend/app/services/misp/feed_map.py`

- [ ] **Step 1:** Call MISP search (restSearch) for value; normalize to `events[]` per spec §4.3.
- [ ] **Step 2:** Build **feed map** from latest `GET /feeds` (id, name, url) cached on request or from explorer cache.
- [ ] **Step 3:** Implement attribution: match event fields to feed (document heuristic); emit detail lines §4.10.8.
- [ ] **Step 4:** Commit: `feat(misp): ioc search and feed attribution`

### Task M5.3: SourceResult builder

**Files:**
- Create: `threatvision/backend/app/schemas/source_result.py`
- Create: `threatvision/backend/app/services/ioc/source_catalog.py`

- [ ] **Step 1:** Define ordered **SOURCE_CATALOG** constant mirroring spec §4.4.
- [ ] **Step 2:** `build_placeholder_results(settings) -> list[SourceResult]` with `not_configured` for missing keys/disabled.
- [ ] **Step 3:** Commit: `feat(ioc): source catalog and placeholders`

---

## Milestone M6 — Enricher adapters + consensus

### Task M6.1: Enricher protocol + first external (e.g. OTX)

**Files:**
- Create: `threatvision/backend/app/services/enrichers/base.py`
- Create: `threatvision/backend/app/services/enrichers/otx.py`

- [ ] **Step 1:** `async def enrich(ctx) -> SourceResult` with timeouts and `unavailable` on failure.
- [ ] **Step 2:** Wire OTX for IP/domain/hash as applicable.
- [ ] **Step 3:** Commit: `feat(enrichers): otx adapter`

### Task M6.2: Remaining enrichers (iterate)

**Files:**
- Create: one file per id under `enrichers/`

- [ ] **Step 1:** Implement VT, AbuseIPDB, Shodan, urlscan, MalwareBazaar, ThreatFox, Safe Browsing, GreyNoise, IBM X-Force with **rate-limit respect** and **N/A** rows per spec.
- [ ] **Step 2:** Mocked HTTP tests per adapter.
- [ ] **Step 3:** Commit per adapter or grouped: `feat(enrichers): external providers`

### Task M6.3: Pipeline orchestration + consensus

**Files:**
- Create: `threatvision/backend/app/services/ioc/pipeline.py`, `consensus.py`
- Create: `threatvision/backend/app/routers/ioc.py`

- [ ] **Step 1:** `async def analyze_ioc(user_id, raw)`: classify → parallel gather (MISP + enabled enrichers) → `aggregate`.
- [ ] **Step 2:** Weighted consensus function (constants in `consensus.py`, tunable later).
- [ ] **Step 3:** `POST /ioc/analyze` returns full JSON schema §4.2; persist `activity_log` with `flagged_by`.
- [ ] **Step 4:** Commit: `feat(ioc): analyze pipeline and consensus`

---

## Milestone M7 — Bulk jobs + SSE

### Task M7.1: Bulk job creation + item storage

**Files:**
- Modify: `threatvision/backend/app/routers/bulk.py`

- [ ] **Step 1:** `POST /ioc/bulk` accepts ≤500 IOCs; create job row + items `pending`.
- [ ] **Step 2:** Background processing: asyncio task queue in-process (v1) or polled worker loop.
- [ ] **Step 3:** Commit: `feat(bulk): job persistence`

### Task M7.2: SSE progress stream

**Files:**
- Create: `threatvision/backend/app/routers/bulk_sse.py`

- [ ] **Step 1:** `GET /ioc/bulk/{job_id}/stream` — `text/event-stream`, emit progress + per-item result as completed.
- [ ] **Step 2:** Client disconnect handling.
- [ ] **Step 3:** Commit: `feat(bulk): sse stream`

---

## Milestone M8 — PDF + Gemini reports

### Task M8.1: HTML template for report

**Files:**
- Create: `threatvision/backend/app/services/reports/templates/report.html` (Jinja2)

- [ ] **Step 1:** Include per-IOC **vendor table** (spec §4.6) + branding footer “Developed by Saichandram Sadhu”.
- [ ] **Step 2:** Commit: `feat(reports): html template`

### Task M8.2: Gemini executive summary

**Files:**
- Create: `threatvision/backend/app/services/reports/gemini.py`

- [ ] **Step 1:** Call Gemini flash with structured prompt; on failure return **placeholder** string (spec §2).
- [ ] **Step 2:** Test with mocked API.
- [ ] **Step 3:** Commit: `feat(reports): gemini summary with degradation`

### Task M8.3: PDF render

**Files:**
- Create: `threatvision/backend/app/services/reports/pdf.py`

- [ ] **Step 1:** Choose WeasyPrint **or** ReportLab; document Dockerfile deps if WeasyPrint.
- [ ] **Step 2:** `POST /reports/pdf` body: analysis ids or inline json → returns `application/pdf` or error if engine fails.
- [ ] **Step 3:** Commit: `feat(reports): pdf generation`

---

## Milestone M9 — SIEM webhooks

### Task M9.1: Generic + Wazuh webhook

**Files:**
- Create: `threatvision/backend/app/routers/webhooks.py`

- [ ] **Step 1:** `POST /api/webhook/siem` — resolve user by **path secret** or **header**; verify optional **HMAC** + timestamp skew ≤5m.
- [ ] **Step 2:** Extract IOC candidates from JSON payload (configurable jsonpath-lite); queue analyze; respond with summary JSON.
- [ ] **Step 3:** Document payload examples in `threatvision/docs/integrations/siem-webhooks.md`.
- [ ] **Step 4:** Commit: `feat(webhooks): siem receiver`

---

## Milestone M10 — Admin / superadmin API

### Task M10.1: Admin routes

**Files:**
- Create: `threatvision/backend/app/routers/admin.py`

- [ ] **Step 1:** List users, set `daily_limit`, `unlimited`, ban, **regenerate API key** (return once), set platform MISP fallback (ADMIN).
- [ ] **Step 2:** Superadmin-only guards using DB role + env email consistency.
- [ ] **Step 3:** Commit: `feat(admin): superadmin controls`

---

## Milestone M11 — Next.js: NextAuth, BFF proxy, UI shell

### Task M11.1: NextAuth configuration

**Files:**
- Create: `threatvision/frontend/lib/auth.ts`, `app/api/auth/[...nextauth]/route.ts`

- [ ] **Step 1:** Providers: Credentials (calls FastAPI login), Google, GitHub; session contains `user.id`, `role`.
- [ ] **Step 2:** Commit: `feat(web): nextauth providers`

### Task M11.2: BFF proxy to FastAPI

**Files:**
- Create: `threatvision/frontend/lib/backend.ts` — `fetchBackend(path, { session })` attaches internal JWT from `POST /internal/auth/exchange` using `BFF_SERVICE_KEY` server-side only.

- [ ] **Step 1:** Implement exchange cached per request (short-lived JWT in memory not stored client-side).
- [ ] **Step 2:** Route handlers under `app/api/threatvision/...` proxy to Railway.
- [ ] **Step 3:** Commit: `feat(web): bff proxy to fastapi`

### Task M11.3: App layout + theme tokens

**Files:**
- Create: `threatvision/frontend/app/globals.css`, `tailwind.config.ts`

- [ ] **Step 1:** CSS variables for palette (spec: void black, cyan, purple, etc.); fonts: Exo 2, Inter, JetBrains Mono.
- [ ] **Step 2:** Commit: `feat(web): design tokens`

---

## Milestone M12 — Login / register cinematic page

### Task M12.1: 3D background + logo

**Files:**
- Create: `threatvision/frontend/components/auth/NebulaBackground.tsx`, `ThreatVisionLogo3D.tsx`, `app/(auth)/login/page.tsx`

- [ ] **Step 1:** R3F particle/nebula + rotating shield logo; **respect** `prefers-reduced-motion`.
- [ ] **Step 2:** Glassmorphism card with email/password + OAuth buttons.
- [ ] **Step 3:** Commit: `feat(ui): cinematic login`

---

## Milestone M13 — Dashboard + MISP Health + activity

### Task M13.1: Dashboard data hooks

**Files:**
- Create: `threatvision/frontend/app/(app)/dashboard/page.tsx`
- Create: `threatvision/frontend/lib/hooks/useDashboardStats.ts`

- [ ] **Step 1:** FastAPI endpoints for aggregates: counts 1d/7d/30d/all, distribution, top IPs (extend backend `routers/stats.py`).
- [ ] **Step 2:** Commit: `feat(api): dashboard stats`

### Task M13.2: MISP Health widget + polling

**Files:**
- Create: `threatvision/frontend/components/dashboard/MispHealthWidget.tsx`

- [ ] **Step 1:** Poll `GET /misp/explorer` every **30s** (or use SSE if implemented); show connected, feeds active/disabled, last sync, total events; link to `/settings/misp`.
- [ ] **Step 2:** Commit: `feat(ui): misp health widget`

### Task M13.3: Recent activity with flagged-by

**Files:**
- Create: `threatvision/frontend/components/dashboard/ActivityFeed.tsx`

- [ ] **Step 1:** `GET /activity/recent` returns spec §4.7 shape.
- [ ] **Step 2:** Render chips for malicious/suspicious sources.
- [ ] **Step 3:** Commit: `feat(ui): activity feed`

### Task M13.4: Globe + GSAP (dashboard polish)

**Files:**
- Create: `threatvision/frontend/components/dashboard/ThreatGlobe.tsx`

- [ ] **Step 1:** R3F globe with threat lat/lng from enriched IPs (backend geo field optional).
- [ ] **Step 2:** GSAP ScrollTrigger sections; number counters.
- [ ] **Step 3:** Commit: `feat(ui): dashboard globe and motion`

---

## Milestone M14 — Settings, MISP Explorer UI, integrations

### Task M14.1: Settings integrations form

**Files:**
- Create: `threatvision/frontend/app/(app)/settings/integrations/page.tsx`

- [ ] **Step 1:** MISP url/key, test button, save encrypted via backend; per-source API keys + toggles + test all.
- [ ] **Step 2:** After successful MISP test, mount **`MispExplorerPanel`** below.
- [ ] **Step 3:** Commit: `feat(ui): integrations settings`

### Task M14.2: Full MISP Explorer page

**Files:**
- Create: `threatvision/frontend/app/(app)/settings/misp/page.tsx`
- Create: `threatvision/frontend/components/misp/FeedsTable.tsx`, `ServersTable.tsx`, `TaxonomiesList.tsx`, `StatsPanel.tsx`, `SyncIndicator.tsx`

- [ ] **Step 1:** Render §4.10.7 layout from explorer DTO.
- [ ] **Step 2:** Live indicator + 30s refresh.
- [ ] **Step 3:** Commit: `feat(ui): misp explorer page`

---

## Milestone M15 — IOC analyze UI (vendor centerpiece)

### Task M15.1: Search bar + results page

**Files:**
- Create: `threatvision/frontend/app/(app)/analyze/page.tsx`, `app/(app)/analyze/[id]/page.tsx` (or query-based)
- Create: `threatvision/frontend/components/ioc/VendorBreakdownTable.tsx`, `ConfidenceGauge.tsx`

- [ ] **Step 1:** Call BFF `POST /ioc/analyze`; render **vendor table** exactly in catalog order; status styling for not_configured / unavailable.
- [ ] **Step 2:** MISP row expandable for **multi-event** list + **feed names** §4.10.8.
- [ ] **Step 3:** IP map with Leaflet (lazy load).
- [ ] **Step 4:** Commit: `feat(ui): ioc results vendor grid`

### Task M15.2: Bulk upload UI + dots

**Files:**
- Create: `threatvision/frontend/app/(app)/bulk/page.tsx`
- Create: `threatvision/frontend/components/ioc/VendorDotsRow.tsx`

- [ ] **Step 1:** Parse CSV/txt; open SSE; table with **dot strip** + tooltips §4.8.
- [ ] **Step 2:** Export buttons: PDF (call backend), CSV, JSON.
- [ ] **Step 3:** Commit: `feat(ui): bulk analysis`

---

## Milestone M16 — Profile, About, admin UI, docs

### Task M16.1: Profile page

**Files:**
- Create: `threatvision/frontend/app/(app)/profile/page.tsx`

- [ ] **Step 1:** API key masked, show/regenerate; usage stats; history list.
- [ ] **Step 2:** Commit: `feat(ui): profile`

### Task M16.2: Admin dashboard

**Files:**
- Create: `threatvision/frontend/app/(app)/admin/page.tsx` (protect by role)

- [ ] **Step 1:** Wire superadmin API actions.
- [ ] **Step 2:** Commit: `feat(ui): admin panel`

### Task M16.3: About + integration guides

**Files:**
- Create: `threatvision/frontend/app/(marketing)/about/page.tsx`
- Create: `threatvision/docs/integrations/wazuh.md`, `siem-webhooks.md`

- [ ] **Step 1:** Mission, flow diagram, stack, credits, OSS notice.
- [ ] **Step 2:** Commit: `docs: about and integration guides`

---

## Milestone M17 — Production hardening

### Task M17.1: CORS, security headers, input sanitize

- [ ] **Step 1:** FastAPI CORS allowlist from `CORS_ORIGINS`; max body size; strip/control chars on IOC input.
- [ ] **Step 2:** Commit: `chore: security hardening`

### Task M17.2: Deploy configs

**Files:**
- Create: `threatvision/frontend/vercel.json` (if needed)
- Create: `threatvision/backend/Dockerfile`, `railway.toml` or README deploy steps

- [ ] **Step 1:** Document env vars for Vercel + Railway.
- [ ] **Step 2:** Commit: `chore: deployment docs and dockerfile`

---

## Milestone M18 — Testing & QA gate

- [x] **Step 1:** Backend: pytest coverage on classify, consensus, rate_limit, misp explorer parsers (fixtures), one enricher e2e mock.
- [x] **Step 2:** Frontend: Playwright smoke (login stub, analyze page renders table).
- [x] **Step 3:** Manual checklist: MISP Docker against explorer + single IOC + feed attribution line.

---

## Execution handoff

**Plan complete** and saved to `threatvision/docs/plans/2026-03-29-threatvision-implementation-plan.md`.

**Option 1 — Subagent-driven:** One fresh subagent per milestone/task with review between tasks.  
**Option 2 — Inline:** Execute milestones in this workspace with checkpoints after M1, M6, M11, M15.

Reply with **1** or **2** (or start with **M0** in this session) when you want implementation to begin.
