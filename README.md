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
- **PostgreSQL** 15+ (local or Docker)

### Environment variables

| Variable | Where | Purpose |
|----------|--------|---------|
| `DATABASE_URL` | Backend | `postgresql://user:pass@host:5432/threatvision` |
| `ENCRYPTION_KEY` | Backend | Fernet key (URL-safe base64, 32-byte) |
| `INTERNAL_JWT_SECRET` | Backend | HS256 secret for BFF ↔ API short-lived JWT |
| `INTERNAL_JWT_EXPIRE_MINUTES` | Backend | Internal JWT TTL (default 5) |
| `BFF_SERVICE_KEY` | Backend + Next server | Shared secret for internal auth exchange only |
| `API_KEY_PEPPER` | Backend | Server secret for HMAC-SHA256 of user API keys (lookup + verify) |
| `SUPERADMIN_EMAIL` | Backend | Email allowed to bootstrap `SUPERADMIN` role |
| `NEXTAUTH_SECRET` | Frontend | NextAuth session encryption |
| `NEXTAUTH_URL` | Frontend | e.g. `http://localhost:3000` |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Frontend | Google OAuth (optional locally) |
| `GITHUB_ID` / `GITHUB_SECRET` | Frontend | GitHub OAuth (optional locally) |
| `NEXT_PUBLIC_APP_URL` | Frontend | Browser-facing app URL |
| `GEMINI_API_KEY` | Backend | Executive summary in PDF (optional) |

### Run two processes

**Terminal 1 — API**

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

## Database migrations

SQL lives in `backend/app/db/migrations/`. Apply `001_initial.sql` with your migration process (or run the statements via `psql`).

**Opt-in integration test (destructive):** resets the **`public`** schema on the target database.

```powershell
$env:TEST_DATABASE_URL = "postgresql://user:pass@localhost:5432/threatvision_test"
$env:RUN_DB_MIGRATION_TESTS = "1"
cd threatvision\backend
.\.venv\Scripts\pytest tests\test_migrations_apply.py::test_migrations_apply_to_database -v
```

## Documentation

- [Design spec](docs/specs/2026-03-29-threatvision-design.md)
- [Implementation plan](docs/plans/2026-03-29-threatvision-implementation-plan.md)

## License

See repository license (to be added).
