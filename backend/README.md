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

## PDF reports (WeasyPrint)

`POST /reports/pdf` renders HTML via **Jinja2** and converts with **WeasyPrint**. On Linux servers (e.g. Railway/Docker), install Cairo, Pango, and GDK-Pixbuf (e.g. Debian/Ubuntu: `apt install libcairo2 libpango-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info`). On Windows, WeasyPrint may require extra GTK/runtime setup; if the engine fails to load, the API returns **503** with `pdf_engine_unavailable`.

Optional **`GEMINI_API_KEY`**: enables the AI executive summary in the PDF; if missing or the API errors, a **placeholder** summary is used and vendor tables are unchanged.
