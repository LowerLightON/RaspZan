# RaspZan Python Rewrite

This is a new modern Python scaffold for rewriting the legacy PHP 5.6 RaspZan application.

The existing legacy PHP project is intentionally left untouched. This repository does not copy PHP code and does not implement legacy business logic yet.

## Stack

- Python 3.12+
- FastAPI
- Jinja2
- PostgreSQL
- SQLAlchemy 2.x
- Alembic
- pydantic-settings
- pytest

## Install Dependencies

```powershell
cd C:\Users\LowerLightON\Documents\Project\raspzan
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Create local settings from the example:

```powershell
Copy-Item .env.example .env
```

## Run Dev Server

```powershell
uvicorn app.main:app --reload
```

Open:

- App: http://127.0.0.1:8000/
- Health: http://127.0.0.1:8000/health
- Legacy inventory summary: http://127.0.0.1:8000/inventory/summary

## Legacy Inventory

The `/inventory/summary` endpoint reads legacy PostgreSQL tables through `LEGACY_DATABASE_URL` from `.env`.

This layer is read-only by design: it uses SQLAlchemy only for `SELECT` queries and does not create Alembic migrations for legacy tables.

## Migration Note

The legacy PHP project in the neighboring `web` directory remains the source of truth for the current production behavior. This scaffold is only the starting point for a controlled rewrite and migration.
