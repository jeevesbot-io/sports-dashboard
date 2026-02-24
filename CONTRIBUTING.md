# Contributing to Sports Dashboard

Thank you for your interest in contributing! This document covers how to set up the project, make changes, and submit them for review.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Commit Style](#commit-style)
- [Pull Requests](#pull-requests)
- [Adding a New Sport Module](#adding-a-new-sport-module)

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20 or 22 LTS (Node 25+ is incompatible with `vue-tsc`)
- PostgreSQL
- Git

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # fill in DATABASE_URL and optional API keys
alembic upgrade head
python app/main.py               # runs on http://localhost:5160
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env             # optional: set VITE_API_BASE_URL
npm run dev                      # runs on http://localhost:5173
```

## Project Structure

```
sports-dashboard/
├── backend/
│   ├── app/
│   │   ├── sports/<sport>/      # one module per sport
│   │   │   ├── models.py        # SQLAlchemy ORM models
│   │   │   ├── schemas.py       # Pydantic request/response schemas
│   │   │   ├── router.py        # FastAPI routes, mounted at /api/<sport>/
│   │   │   ├── service.py       # business logic and DB queries
│   │   │   ├── client.py        # external API client
│   │   │   ├── ingestion.py     # data sync
│   │   │   ├── scrapers/        # web scrapers
│   │   │   ├── predictions.py   # statistical model
│   │   │   └── projections.py   # Monte Carlo projections
│   │   ├── common/
│   │   │   ├── schemas.py       # StandardResponse wrapper
│   │   │   └── dependencies.py  # shared FastAPI dependencies
│   │   ├── config.py            # Pydantic Settings (reads .env)
│   │   ├── db.py                # async SQLAlchemy engine + get_db
│   │   └── main.py              # app entry point
│   └── tests/
└── frontend/
    └── src/
        ├── api/index.ts         # single Axios client for all backend calls
        ├── stores/              # Pinia stores
        ├── views/               # page-level components
        ├── components/          # reusable components
        ├── types/index.ts       # shared TypeScript interfaces
        └── router/index.ts      # Vue Router (lazy-loaded routes)
```

## Making Changes

### Backend conventions

- All API responses must use `StandardResponse` from `common/schemas.py`:
  `{ success, message, data, errors, timestamp }`
- Business logic belongs in `service.py`; routers should only handle HTTP concerns.
- Use `async`/`await` throughout — the stack is fully async (asyncpg + SQLAlchemy async).
- ORM models inherit from `Base` in `db.py`, which already provides `created_at` and
  `updated_at` — do not redefine them in child models.
- Add Pydantic schemas for every new request/response shape in `schemas.py`.
- New endpoints follow the pattern `GET /api/<sport>/<resource>`.

### Frontend conventions

- All HTTP calls go through `api/index.ts`. Do not create a second API client or use
  raw `fetch()`.
- Use Vue 3 Composition API with `<script setup lang="ts">`.
- TypeScript strict mode is enabled — add types to `types/index.ts` for shared shapes.
- Pinia store methods call `apiClient.get*()` which return unwrapped data.
- Analytics components that call the API directly receive a `StandardResponse<T>` — access
  `.data` for the payload and `.message` for metadata (e.g. to detect mock data).
- Use path alias `@/` instead of relative paths when importing from `src/`.
- UI primitives come from PrimeVue; charts use ECharts via `vue-echarts`.

## Testing

### Backend tests

Tests use `pytest` + `pytest-asyncio` with an in-memory SQLite database. No external
services or PostgreSQL are required.

```bash
cd backend && source .venv/bin/activate

# Run the full suite
python -m pytest tests/ -v --asyncio-mode=auto

# Run a single file
python -m pytest tests/test_football_service.py -v --asyncio-mode=auto

# Run a specific test
python -m pytest tests/test_football_service.py::test_name -v --asyncio-mode=auto
```

Always pass `--asyncio-mode=auto`. New tests should follow the patterns in `tests/conftest.py`
(async fixtures, `httpx.AsyncClient` via `ASGITransport`).

### Frontend

Currently the project has Playwright e2e tests in `frontend/e2e/`. Run them with:

```bash
cd frontend
npx playwright test
```

Type-check the frontend without running the full build:

```bash
cd frontend
npm run type-check    # requires Node 20/22
# or, on Node 25+:
npx vite build
```

Lint (auto-fixes where possible):

```bash
cd frontend
npm run lint
```

## Commit Style

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <short description>
```

Common types:

| Type       | When to use                                    |
|------------|------------------------------------------------|
| `feat`     | New feature visible to users                   |
| `fix`      | Bug fix                                        |
| `docs`     | Documentation only                             |
| `refactor` | Code change that is neither a fix nor a feature|
| `test`     | Adding or updating tests                       |
| `chore`    | Build scripts, CI, dependency updates          |
| `perf`     | Performance improvement                        |

Keep the subject line under 72 characters. Add a body for non-obvious context.

## Pull Requests

1. Branch from `dev` (or the relevant feature branch):
   ```bash
   git checkout dev
   git pull
   git checkout -b feat/my-feature
   ```
2. Make focused, atomic commits.
3. Ensure all backend tests pass before opening a PR.
4. Run `npm run lint` and fix any errors.
5. Open a PR targeting `dev`. The `main` branch is for stable releases only.
6. Describe *what* changed and *why* in the PR body. Link any related issues.

## Adding a New Sport Module

Cricket and rugby stubs already exist. To flesh out a sport:

1. **Backend** — populate `backend/app/sports/<sport>/` following the football module as a
   reference. Register the router in `app/main.py`.
2. **Frontend** — add views under `src/views/<sport>/`, register routes in
   `src/router/index.ts`, and add the sport to `AppSidebar.vue`.
3. **Tests** — add a `tests/test_<sport>_service.py` mirroring `test_football_service.py`.
4. **Database** — create an Alembic migration for any new tables:
   ```bash
   cd backend
   alembic revision --autogenerate -m "add <sport> tables"
   alembic upgrade head
   ```

## Known Limitations

- The **Understat** scraper falls back to mock data when scraping fails. The xG standings
  endpoint includes `"mock"` in the response `message` when mock data is returned.
- The **FBref** scraper requires `beautifulsoup4` and falls back to mock data if scraping
  fails or BS4 is unavailable. It is rate-limited at 5 s between requests.
- `vue-tsc` is incompatible with Node.js 25+. Use Node 20 or 22 LTS for full type-checking.
