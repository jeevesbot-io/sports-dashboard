# Sports Analytics Dashboard

A full-stack multi-sport analytics platform providing advanced statistics, predictions, and visualizations for football (soccer). The system features xG (expected goals) analysis, Monte Carlo season projections, Poisson-based match predictions, and comprehensive performance metrics.

**Status:** Football module is fully implemented with real-time data ingestion, advanced analytics, and prediction tracking. Cricket and rugby modules are stubs for future development.

## Features

### Football Analytics
- **xG Analysis** — Expected goals tracking, team performance analysis, over/under-performance detection
- **Match Predictions** — Poisson model-based predictions with win/draw/loss probabilities
- **Season Projections** — Monte Carlo simulations for final league positions and outcomes
- **Advanced Statistics** — FBref integration for progressive passes, pressures, and tactical metrics
- **Player Analytics** — Individual player stats with sorting, filtering, and team comparisons
- **Head-to-Head** — Historical matchup analysis with detailed records
- **Form Analysis** — Opponent-adjusted form ratings and recent performance tracking
- **Home Advantage** — Multi-season home/away performance analysis
- **Fixture Difficulty** — Visual heatmap of upcoming opponent strength
- **Position Progression** — League table movement tracking by matchday

## Tech Stack

### Backend
- **FastAPI** — Modern async Python web framework
- **SQLAlchemy 2.x** — Async ORM with full type support
- **PostgreSQL** — Production database with asyncpg driver
- **Alembic** — Database migrations
- **Pydantic** — Request/response validation and settings management
- **pytest + pytest-asyncio** — Testing framework with async support

### Frontend
- **Vue 3** — Composition API with `<script setup>` syntax
- **TypeScript** — Strict mode type checking
- **Pinia** — State management
- **Vue Router** — Client-side routing with lazy loading
- **PrimeVue** — UI component library
- **ECharts** — Data visualization (via vue-echarts)
- **Vite** — Build tool and dev server
- **Tailwind CSS** — Utility-first CSS framework

### Data Sources
- **football-data.org** — Fixtures, standings, team data
- **Understat** — xG data and player statistics (web scraping)
- **FBref** — Advanced tactical and performance metrics (web scraping)

## Architecture

### Project Structure

```
sports-dashboard/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── config.py            # Settings and environment config
│   │   ├── db.py                # Database engine and session setup
│   │   ├── common/              # Shared utilities
│   │   │   ├── schemas.py       # StandardResponse wrapper
│   │   │   └── dependencies.py  # FastAPI dependencies
│   │   └── sports/              # Sport modules
│   │       ├── football/        # Football module (fully implemented)
│   │       │   ├── models.py    # SQLAlchemy ORM models
│   │       │   ├── schemas.py   # Pydantic request/response schemas
│   │       │   ├── router.py    # API route handlers
│   │       │   ├── service.py   # Business logic layer
│   │       │   ├── client.py    # External API client (football-data.org)
│   │       │   ├── ingestion.py # Data sync from external APIs
│   │       │   ├── predictions.py # Poisson match prediction model
│   │       │   ├── projections.py # Monte Carlo season simulator
│   │       │   └── scrapers/    # Web scrapers (Understat, FBref)
│   │       ├── cricket/         # Cricket module (stub)
│   │       └── rugby/           # Rugby module (stub)
│   ├── alembic/                 # Database migrations
│   ├── tests/                   # Test suite
│   └── requirements.txt         # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── main.ts              # Vue application entry point
│   │   ├── App.vue              # Root component
│   │   ├── router/              # Vue Router configuration
│   │   ├── stores/              # Pinia state management
│   │   │   └── football.ts      # Football store (teams, fixtures, standings)
│   │   ├── api/                 # API client
│   │   │   └── index.ts         # Axios client with StandardResponse unwrapping
│   │   ├── types/               # TypeScript interfaces
│   │   ├── views/               # Page components
│   │   │   └── football/        # Football views (Dashboard, Analytics, TeamDetail)
│   │   ├── components/          # Reusable components
│   │   │   └── football/        # Football-specific components (charts, predictions)
│   │   └── composables/         # Vue composables
│   ├── public/                  # Static assets
│   └── package.json             # Node dependencies
└── CLAUDE.md                    # Developer documentation for AI assistants
```

### Data Flow

```
External APIs (football-data.org, Understat, FBref)
    ↓ (ingestion endpoints)
PostgreSQL Database ← SQLAlchemy ORM ← Service Layer ← FastAPI Router
    ↓ (API requests)
Axios API Client → Pinia Store → Vue Components → ECharts Visualizations
```

### Sport Module Pattern

Each sport follows a consistent structure:
- **models.py** — Database schema (SQLAlchemy ORM)
- **schemas.py** — API contracts (Pydantic models)
- **router.py** — HTTP endpoints (FastAPI routes)
- **service.py** — Business logic and database queries
- **client.py** — External API integration
- **ingestion.py** — Data synchronization
- **scrapers/** — Web scraping modules

All API responses use `StandardResponse` wrapper:
```json
{
  "success": true,
  "message": "Retrieved 20 teams",
  "data": [...],
  "errors": null,
  "timestamp": "2025-02-24T20:18:00Z"
}
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+ (note: vue-tsc has compatibility issues with Node 25+)
- PostgreSQL 14+
- Git

### Clone the Repository

```bash
git clone https://github.com/jeevesbot-io/sports-dashboard.git
cd sports-dashboard
```

**Note:** The default branch is `dev`. Use `git checkout main` for the stable release.

### Backend Setup

1. **Create a virtual environment:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Configure environment:**

```bash
cp .env.example .env
```

Edit `.env` and set your database connection:
```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
FOOTBALL_DATA_API_KEY=your_api_key_here  # Optional for basic development
CURRENT_SEASON=2025
```

**Note:** `FOOTBALL_DATA_API_KEY` is optional for basic development. The API is used for data ingestion but not required to run the application or view existing data.

4. **Run database migrations:**

```bash
cd backend
alembic upgrade head
```

5. **Start the development server:**

```bash
# From backend/ directory with venv activated
python app/main.py

# Or using uvicorn directly:
uvicorn app.main:app --reload --port 5160
```

The API will be available at `http://localhost:5160`

### Frontend Setup

1. **Install dependencies:**

```bash
cd frontend
npm install
```

2. **Configure environment (optional):**

```bash
cp .env.example .env
```

Edit `.env` if your backend is not on the default port:
```bash
VITE_API_BASE_URL=http://localhost:5160
```

3. **Start the development server:**

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Initial Data Ingestion

Once both servers are running, trigger data ingestion:

```bash
# Ingest core data (teams, fixtures, standings)
curl -X POST "http://localhost:5160/api/football/ingest?season=2025"

# Ingest xG data from Understat
curl -X POST "http://localhost:5160/api/football/ingest-xg?season=2025"

# Ingest player statistics
curl -X POST "http://localhost:5160/api/football/ingest-players?season=2025"

# Ingest advanced stats from FBref
curl -X POST "http://localhost:5160/api/football/ingest-fbref?season=2025"
```

## API Documentation

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/football/teams` | List all teams |
| `GET` | `/api/football/teams/{team_id}` | Get team details with statistics |
| `GET` | `/api/football/teams/{team_id}/form` | Team form analysis (recent N games) |
| `GET` | `/api/football/fixtures` | Get fixtures with filtering |
| `GET` | `/api/football/standings` | League table standings |

### Analytics Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/football/xg/standings` | xG-based league table |
| `GET` | `/api/football/xg/overperformers` | Teams over/under-performing xG |
| `GET` | `/api/football/teams/{team_id}/xg` | Team-specific xG analysis |
| `GET` | `/api/football/teams/{team_id}/xg-timeline` | Match-by-match xG progression |
| `GET` | `/api/football/teams/{team_id}/vs-league` | Team vs league average comparison |
| `GET` | `/api/football/head-to-head` | Head-to-head record between teams |
| `GET` | `/api/football/home-advantage` | Home advantage index for all teams |
| `GET` | `/api/football/home-advantage-multi-season` | Multi-season home/away performance |

### Prediction Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/football/predict` | Poisson model match prediction |
| `GET` | `/api/football/projections` | Monte Carlo season projections |
| `GET` | `/api/football/upcoming` | Upcoming fixtures with optional predictions |
| `POST` | `/api/football/predictions/store` | Store prediction for accuracy tracking |
| `GET` | `/api/football/predictions/accuracy` | Prediction accuracy statistics |
| `GET` | `/api/football/predictions/history` | Historical prediction records |

### Advanced Stats Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/football/players` | Player statistics with filtering/sorting |
| `GET` | `/api/football/players/{player_id}` | Individual player details |
| `GET` | `/api/football/advanced/teams` | FBref advanced team stats |
| `GET` | `/api/football/advanced/players` | FBref advanced player stats |
| `GET` | `/api/football/team-ratings` | Multi-season team strength ratings |
| `GET` | `/api/football/teams/{team_id}/form-adjusted` | Opponent-adjusted form rating |
| `GET` | `/api/football/teams/{team_id}/scorelines` | Most common scoreline patterns |
| `GET` | `/api/football/fixture-difficulty` | Upcoming fixture difficulty heatmap |

### Chart Data Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/football/charts/points-progression` | Cumulative points by matchday |
| `GET` | `/api/football/charts/form-heatmap` | Recent form visualization data |
| `GET` | `/api/football/charts/position-progression` | League position by matchday |

### Data Ingestion Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/football/ingest` | Sync teams, fixtures, standings |
| `POST` | `/api/football/ingest-xg` | Scrape xG data from Understat |
| `POST` | `/api/football/ingest-players` | Scrape player stats from Understat |
| `POST` | `/api/football/ingest-fbref` | Scrape advanced stats from FBref |
| `POST` | `/api/football/ingest-multi-season` | Ingest data for multiple seasons |
| `POST` | `/api/football/predictions/update-results` | Update predictions with actual results |

All endpoints return responses wrapped in `StandardResponse`:
```typescript
{
  success: boolean;
  message: string;
  data: T;
  errors?: string[];
  timestamp: string;
}
```

Interactive API documentation is available at `http://localhost:5160/docs` (Swagger UI) and `http://localhost:5160/redoc` (ReDoc).

## Testing

### Backend Tests

The test suite uses pytest with async support and in-memory SQLite (no PostgreSQL required for testing).

**Run all tests:**
```bash
cd backend
source .venv/bin/activate
python -m pytest tests/ -v --asyncio-mode=auto
```

**Run a specific test file:**
```bash
python -m pytest tests/test_football_service.py -v --asyncio-mode=auto
```

**Run a specific test:**
```bash
python -m pytest tests/test_football_service.py::test_get_teams -v --asyncio-mode=auto
```

**Important:** Always include `--asyncio-mode=auto` when running pytest. The test suite uses async fixtures and requires this flag.

### Test Architecture

- **conftest.py** — Provides async fixtures for database engine, session, and HTTPX test client
- **In-memory SQLite** — Tests use `aiosqlite` instead of PostgreSQL for speed and isolation
- **ASGITransport** — HTTPX test client overrides the `get_db` dependency for isolated test sessions
- **No external services** — All tests are fully self-contained

## Development Notes

### Default Branch

- **Development:** `dev` (default branch)
- **Production:** `main` (stable releases)

### Port Configuration

- **Backend API:** `http://localhost:5160`
- **Frontend Dev Server:** `http://localhost:5173`
- **CORS:** Configured to allow `localhost:3000`, `localhost:5173-5175`, and `localhost:8080`

### Node.js Compatibility

**Known Issue:** `vue-tsc` (TypeScript checker for Vue) is incompatible with Node.js 25+.

**Workarounds:**
- Use Node.js 20 or 22 LTS for full type-checking support
- Or skip type-checking during build: `npx vite build` instead of `npm run build`
- The dev server (`npm run dev`) works fine on all Node versions

### Database Configuration

The backend uses SQLAlchemy's async engine with PostgreSQL. The `Base` model class automatically provides `created_at` and `updated_at` columns — child models should **not** redefine these fields.

### API Client Pattern

Frontend components should **only** use the centralized API client at `src/api/index.ts`. Do not create additional API clients or use raw `fetch()`.

- **Pinia stores** call `apiClient.getFootball*()` methods which return unwrapped data
- **Analytics components** call methods that return `StandardResponse<T>` — access the `.data` property for the payload

### Season Configuration

The current season is configured in `backend/.env` as `CURRENT_SEASON=2025`. All service methods use this value by default but accept an optional `season` parameter for historical data queries.

## Known Limitations

### Data Source Limitations

- **Understat scraper** — Falls back to mock data when scraping fails. The xG standings endpoint includes "mock" in the response message when mock data is detected. The frontend shows a "Mock Data" badge when this occurs.
- **FBref scraper** — Requires `beautifulsoup4` for HTML parsing. Falls back to mock data if scraping fails or dependencies are unavailable. Rate-limited to 5 seconds between requests to avoid IP blocking.
- **football-data.org** — Free tier has rate limits and may not include all historical data.

### Deferred Features

The following features are documented but not yet implemented:

- **Set Piece Analysis** — Requires event-level data not available from current sources
- **Key Player Impact** — Requires per-match lineup data from individual Understat match pages
- **Cricket Module** — Stub only, no implementation
- **Rugby Module** — Stub only, no implementation

### Performance Considerations

- **Monte Carlo projections** — Default 1,000 simulations. Can be increased to 10,000 for better accuracy but significantly increases response time.
- **Multi-season queries** — Queries spanning 3+ seasons may be slow on large datasets. Consider indexing strategies for production deployments.

## Contributing

1. Create a feature branch from `dev`: `git checkout -b feature/your-feature-name`
2. Make your changes following the existing patterns
3. Write tests for new functionality
4. Run the test suite: `pytest tests/ -v --asyncio-mode=auto`
5. Submit a pull request to `dev` (not `main`)

## License

TBD
