# RaspZan Developer Setup

Short local setup guide for backend development.

## Requirements

- Python 3.12+
- PostgreSQL 16 recommended
- Git

## Clone

```powershell
git clone <repo-url>
cd raspzan
```

## Create Virtual Environment

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\activate
```

## Install Dependencies

For normal development, install the project in editable mode with dev dependencies:

```powershell
pip install -e ".[dev]"
```

The project uses `pyproject.toml` as the single source for package metadata and dependencies. There is no `requirements.txt`; runtime dependencies live in `[project.dependencies]`, and test/dev dependencies live in `[project.optional-dependencies].dev`.

For runtime-only installation:

```powershell
pip install -e .
```

## Environment Variables

Local settings are loaded from `.env` in the project root.

Create it from the example:

```powershell
Copy-Item .env.example .env
```

Minimum local variables:

```env
APP_NAME=RaspZan
ENVIRONMENT=local
DEBUG=true
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/raspzan
LEGACY_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/2526
SECRET_KEY=change-me
```

`DATABASE_URL` points to the new application database. `LEGACY_DATABASE_URL` is only for read-only legacy inspection endpoints and is not used by new migrations.

## Database Migrations

Make sure PostgreSQL is running and the `raspzan` database exists, then apply migrations:

```powershell
python -m alembic upgrade head
```

Migrations create and evolve the new application schema. Do not use Alembic for legacy tables.

## Dev Seed

Load minimal development data:

```powershell
python -m app.scripts.seed_dev
```

The seed creates roles, a test planner user, faculty, department, group, teacher, building, room, subject, lesson plan, and lesson plan item. It is idempotent, so repeated runs should not create duplicates.

## Run Server

```powershell
uvicorn app.main:app --reload
```

Useful local URLs:

- App: http://127.0.0.1:8000/
- Health: http://127.0.0.1:8000/health
- OpenAPI: http://127.0.0.1:8000/docs

## Tests

```powershell
python -m pytest
```

## Architecture Overview

```text
Router
 -> Application Services
    -> Conflict Engine
       -> Isolated Validators
    -> Query Services
       -> ScheduleQueryOptions
       -> DB
```

Routers should stay thin: request parsing, service call, response formatting. Scheduling rules belong in services, conflict validators, or query services, not in routes.
