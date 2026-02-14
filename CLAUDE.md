# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full-stack multi-sport analytics dashboard. Monorepo with a FastAPI (Python) backend and Vue 3 (TypeScript) frontend. Currently football is the only fully implemented sport; cricket and rugby modules are stubs.

## Commands

### Backend

```bash
# Start dev server (from repo root)
cd backend && source .venv/bin/activate && python app/main.py
# Or: uvicorn app.main:app --reload --port 5060

# Run all tests
cd backend && source .venv/bin/activate && pytest tests/

# Run a single test file
pytest backend/tests/test_football_service.py

# Run a specific test
pytest backend/tests/test_football_service.py::test_name -v

# Tests use async mode — add --asyncio-mode=auto if needed
# Tests use in-memory SQLite (no Postgres required)

# Install dependencies
cd backend && pip install -r requirements.txt

# Database migrations
cd backend && alembic upgrade head
```

### Frontend

```bash
cd frontend

npm run dev          # Vite dev server on localhost:5173
npm run build        # Type-check + production build
npm run lint         # ESLint with auto-fix (.vue, .ts, .tsx, .js, .jsx)
npm run type-check   # vue-tsc --noEmit
npm run preview      # Preview production build
```

## Architecture

### Backend (`backend/app/`)

FastAPI app with fully async SQLAlchemy + PostgreSQL (asyncpg). Entry point is `app/main.py`.

**Sport module pattern** (`app/sports/<sport>/`):
- `models.py` — SQLAlchemy ORM models
- `schemas.py` — Pydantic request/response schemas
- `router.py` — FastAPI route handlers, mounted at `/api/<sport>/`
- `service.py` — Business logic layer; all DB queries live here
- `client.py` — External API client (football-data.org)
- `ingestion.py` — Data sync from external APIs
- `scrapers/` — Web scrapers (e.g., Understat for xG data)
- `predictions.py` — Poisson model match predictions

**Key wiring:**
- `config.py` — Pydantic `Settings` class, reads from `.env` (see `.env.example`)
- `db.py` — Async engine/session setup; `get_db` dependency for injection
- `common/schemas.py` — `StandardResponse` wrapper used by all endpoints
- `common/dependencies.py` — Shared FastAPI dependencies (pagination, validation)
- CORS allows localhost ports 3000, 5173-5175, 8080
- Backend runs on port **5060** by default

**All API responses use `StandardResponse`:** `{ success, message, data, errors, timestamp }`

### Frontend (`frontend/src/`)

Vue 3 with Composition API (`<script setup>`), TypeScript strict mode, Pinia for state, Vue Router with lazy-loaded routes, PrimeVue components, and ECharts (via vue-echarts) for visualization.

**Key structure:**
- `api/index.ts` — Axios client with logging interceptors; proxied to backend via Vite config
- `stores/football.ts` — Pinia store: teams, standings, fixtures, form analysis
- `views/football/` — Dashboard, TeamDetail, Analytics pages
- `components/football/` — Chart components (XgChart, FormHeatmap, PointsProgression, etc.)
- `types/index.ts` — Shared TypeScript interfaces
- Path alias: `@/` maps to `src/`

### Data Flow

```
Vue component → Pinia store action → Axios → FastAPI router → Service layer → SQLAlchemy → PostgreSQL
```

External data comes in via `POST /api/football/ingest` (Football Data API) and `POST /api/football/ingest-xg` (Understat scraper).

## Testing

Backend tests use `pytest` + `pytest-asyncio` with in-memory SQLite via `aiosqlite`. The test `conftest.py` provides async fixtures for engine, session, and an `httpx.AsyncClient` that overrides the `get_db` dependency. No external services or Postgres needed for tests.

## Environment

Backend requires a `.env` file in `backend/` (template: `.env.example`). Key variables:
- `DATABASE_URL` — PostgreSQL connection string (default: `postgresql+asyncpg://jeeves@localhost/jeeves`)
- `FOOTBALL_DATA_API_KEY` — API key for football-data.org (optional for basic dev)

## Git

- `main` branch is the PR target
- Current development is on `dev`
