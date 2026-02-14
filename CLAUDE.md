# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full-stack multi-sport analytics dashboard. Monorepo with a FastAPI (Python) backend and Vue 3 (TypeScript) frontend. Currently football is the only fully implemented sport; cricket and rugby modules are stubs.

## Commands

### Backend

```bash
# Start dev server (from repo root)
cd backend && source .venv/bin/activate && python app/main.py
# Or: uvicorn app.main:app --reload --port 5160

# Run all tests
cd backend && source .venv/bin/activate && python -m pytest tests/ -v --asyncio-mode=auto

# Run a single test file
cd backend && source .venv/bin/activate && python -m pytest tests/test_football_service.py

# Run a specific test
cd backend && source .venv/bin/activate && python -m pytest tests/test_football_service.py::test_name -v

# Tests use async mode — always pass --asyncio-mode=auto
# Tests use in-memory SQLite (no Postgres required)
# httpx test client uses ASGITransport (see conftest.py)

# Install dependencies
cd backend && pip install -r requirements.txt

# Database migrations
cd backend && alembic upgrade head
```

### Frontend

```bash
cd frontend

npm run dev          # Vite dev server on localhost:5173
npm run build        # Type-check + production build (vue-tsc requires compatible Node)
npm run lint         # ESLint with auto-fix (.vue, .ts, .tsx, .js, .jsx)
npm run type-check   # vue-tsc --noEmit (requires Node <25 due to vue-tsc compat)
npm run preview      # Preview production build
```

**Note:** `vue-tsc` is incompatible with Node.js 25+. Use `npx vite build` to verify compilation without the vue-tsc step, or use Node 20/22 LTS for full type-checking.

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
- `scrapers/` — Web scrapers (Understat for xG + player data, FBref for advanced stats)
- `predictions.py` — Poisson model match predictions
- `projections.py` — Monte Carlo season outcome projections

**Key wiring:**
- `config.py` — Pydantic `Settings` class, reads from `.env` (see `.env.example`). Contains `current_season` setting used by all service methods.
- `db.py` — Async engine/session setup; `get_db` dependency for injection. `Base` model provides `created_at`/`updated_at` columns — child models should NOT redefine them.
- `common/schemas.py` — `StandardResponse` wrapper used by all endpoints
- `common/dependencies.py` — Shared FastAPI dependencies (pagination, validation)
- CORS allows localhost ports 3000, 5173-5175, 8080
- Backend runs on port **5160** by default

**All API responses use `StandardResponse`:** `{ success, message, data, errors, timestamp }`

### Frontend (`frontend/src/`)

Vue 3 with Composition API (`<script setup>`), TypeScript strict mode, Pinia for state, Vue Router with lazy-loaded routes, PrimeVue components, and ECharts (via vue-echarts) for visualization.

**Key structure:**
- `api/index.ts` — **Single Axios API client** for all backend calls (core + analytics). All methods unwrap `StandardResponse` and return typed data. There is no second API client — do NOT create `services/api.ts`.
- `stores/football.ts` — Pinia store: teams, standings, fixtures, form analysis. Uses `api/index.ts` for data fetching.
- `views/football/` — Dashboard, TeamDetail, Analytics pages
- `components/football/` — Chart components (XgChart, XgTimeline, FormHeatmap, PointsProgression, HomeAdvantageChart, SeasonTracker, TeamVsLeague, SeasonProjections, AdvancedStatsTable, PlayerDashboard), HeadToHead, MatchPredictor, FixtureList
- `types/index.ts` — Shared TypeScript interfaces including analytics types (XGStanding, HeadToHeadData, MatchPrediction, TeamXGAnalysis, ChartData, HomeAdvantageData, PlayerStats, TeamProjection, AdvancedTeamStats, etc.)
- Path alias: `@/` maps to `src/`

**API client patterns:**
- Pinia store methods call `apiClient.getFootball*()` which return unwrapped data (e.g., `FootballTeam[]`)
- Analytics components call `apiClient.getXGStandings()` etc. which return `StandardResponse<T>` — access `.data` for the payload, `.message` for metadata
- Never create a second API client or use raw `fetch()` — all calls go through `api/index.ts`

### Data Flow

```
Vue component → Pinia store action → Axios → FastAPI router → Service layer → SQLAlchemy → PostgreSQL
```

For analytics views (AnalyticsView, HeadToHead, MatchPredictor), components call `api/index.ts` directly instead of going through the Pinia store.

External data comes in via `POST /api/football/ingest` (Football Data API), `POST /api/football/ingest-xg` (Understat xG scraper), `POST /api/football/ingest-players` (Understat player data), and `POST /api/football/ingest-fbref` (FBref advanced stats).

## Testing

Backend tests use `pytest` + `pytest-asyncio` with in-memory SQLite via `aiosqlite`. The test `conftest.py` provides async fixtures for engine, session, and an `httpx.AsyncClient` (via `ASGITransport`) that overrides the `get_db` dependency. No external services or Postgres needed for tests.

Always run tests with: `python -m pytest tests/ -v --asyncio-mode=auto`

## Environment

Backend requires a `.env` file in `backend/` (template: `.env.example`). Key variables:
- `DATABASE_URL` — PostgreSQL connection string (default: `postgresql+asyncpg://jeeves@localhost/jeeves`)
- `FOOTBALL_DATA_API_KEY` — API key for football-data.org (optional for basic dev)
- `CURRENT_SEASON` — Season year (default: 2025)

Frontend has an optional `.env` file (template: `frontend/.env.example`):
- `VITE_API_BASE_URL` — Backend URL (default: `http://localhost:5160`)

## Git

- `main` branch is the PR target
- Current development is on `dev`

## Known Limitations

- **Understat scraper** falls back to mock data when scraping fails. The xG standings endpoint includes "mock" in the response message when mock data is detected. The frontend AnalyticsView shows a "Mock Data" tag when this is detected.
- **FBref scraper** requires `beautifulsoup4` for HTML parsing. Falls back to mock data if scraping fails or BS4 is unavailable. Rate-limited at 5s between requests.
- **Set Piece Analysis** — deferred; requires event-level data not available from current sources.
- **Key Player Impact** — deferred; requires per-match lineup data from individual Understat match pages.
