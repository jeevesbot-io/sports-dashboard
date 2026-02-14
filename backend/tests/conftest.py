"""
Pytest configuration and fixtures for the Sports Dashboard API.
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db import get_db, Base
from app.config import settings

# Test database URL (in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def engine():
    """Create test database engine."""
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield test_engine
    
    # Clean up
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    TestSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False
    )
    
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_team_data():
    """Sample team data for testing."""
    return {
        "api_id": 12345,
        "name": "Newcastle United",
        "short_name": "Newcastle",
        "tla": "NEW",
        "crest_url": "https://example.com/crest.png"
    }


@pytest.fixture
def sample_fixture_data():
    """Sample fixture data for testing."""
    return {
        "api_id": 67890,
        "season": 2025,
        "matchday": 1,
        "status": "FINISHED",
        "home_score": 2,
        "away_score": 1,
        "winner": "HOME"
    }


@pytest.fixture
def sample_standing_data():
    """Sample standing data for testing."""
    return {
        "season": 2025,
        "matchday": 1,
        "position": 1,
        "played": 1,
        "won": 1,
        "drawn": 0,
        "lost": 0,
        "goals_for": 2,
        "goals_against": 1,
        "goal_difference": 1,
        "points": 3,
        "form": "W"
    }