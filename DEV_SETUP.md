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

Load demo schedule data for visually checking Schedule Explorer table and grid views:

```powershell
python -m app.scripts.seed_demo_schedule
```

The demo schedule uses group `DEV-101`, dates `2026-05-04` through `2026-05-09`, several periods, and one stacked grid slot.

## Run Server

```powershell
uvicorn app.main:app --reload
```

Useful local URLs:

- App: http://localhost:8000/
- Health: http://localhost:8000/health
- OpenAPI / Swagger: http://localhost:8000/docs

## Frontend Setup

The React frontend lives in `frontend/` and uses Vite, TypeScript, and TanStack Query.

Install dependencies and verify the production build:

```powershell
cd frontend
npm install
npm run build
```

Run the frontend development server:

```powershell
npm run dev
```

Use this dev URL:

```text
http://localhost:5173
```

Use `localhost`, not `127.0.0.1`, because the backend CORS configuration allows the frontend dev origin `http://localhost:5173`.

## Backend + Frontend Local Dev

Run the backend and frontend in two separate terminals.

Terminal 1 - backend:

```powershell
cd C:\Users\LowerLightON\Documents\Project\raspzan
.\.venv\Scripts\activate
uvicorn app.main:app --reload
```

Backend URLs:

```text
http://localhost:8000
http://localhost:8000/docs
```

Terminal 2 - frontend:

```powershell
cd C:\Users\LowerLightON\Documents\Project\raspzan\frontend
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

## Docker Compose

Docker is an optional local development workflow. The normal virtual environment workflow above remains the primary setup path.

Start PostgreSQL:

```powershell
docker compose up -d db
```

Apply migrations manually:

```powershell
docker compose run --rm app python -m alembic upgrade head
```

Run the app:

```powershell
docker compose up app
```

Run tests:

```powershell
docker compose run --rm app python -m pytest
```

Load development seed data:

```powershell
docker compose run --rm app python -m app.scripts.seed_dev
```

Load demo schedule data:

```powershell
docker compose run --rm app python -m app.scripts.seed_demo_schedule
```

The Docker app container uses `DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/raspzan`. Migrations are not run automatically by the container entrypoint.

## Tests

Backend:

```powershell
python -m pytest
```

Docker:

```powershell
docker compose run --rm app python -m pytest
```

Frontend:

```powershell
cd frontend
npm run build
```

## Git Notes

Do not commit generated or local-only files:

- `frontend/node_modules/`
- `frontend/dist/`
- `.env`
- `.venv`
- `.pytest_cache`

Check ignored files when needed:

```powershell
git status --ignored
```

## CI

GitHub Actions runs migrations and tests against a PostgreSQL service using Python 3.12:

```text
python -m alembic upgrade head
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
