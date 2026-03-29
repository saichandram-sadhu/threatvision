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
