"""Shared fixtures for RLHF package tests."""

import os

# Override DATABASE_URL before any archive_api imports so the module-level
# engine in database.py uses SQLite instead of PostgreSQL.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest_asyncio.fixture
async def engine():
    """In-memory SQLite engine with tables created."""
    eng = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    from archive_api.models.database import Base

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine):
    """Async session bound to the test engine."""
    factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(engine):
    """HTTPX AsyncClient with FastAPI app and get_db override."""
    from archive_api.models.database import get_db
    from archive_api.main import app

    factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_expert(client):
    """Register a sample expert via API."""
    resp = await client.post(
        "/experts/register",
        json={
            "username": "dr_smith",
            "display_name": "Dr. Smith",
            "subspecialty": "neuromuscular",
            "patient_categories": ["neuromuscular", "metabolic"],
        },
    )
    assert resp.status_code == 200
    return resp.json()


@pytest_asyncio.fixture
async def sample_evaluation(client, sample_expert):
    """Submit a sample evaluation via API."""
    resp = await client.post(
        "/evaluations/submit",
        json={
            "expert_username": "dr_smith",
            "case_id": "CASE001",
            "patient_category": "neuromuscular",
            "model_a_id": "model-A",
            "model_b_id": "model-B",
            "model_a_response": "Response A is detailed.",
            "model_b_response": "Response B is brief.",
            "winner": "a",
            "model_a_annotations": {
                "diagnostic_accuracy": 4,
                "reasoning_quality": 3,
                "tool_usage": 2,
                "safety": 5,
            },
            "model_b_annotations": {
                "diagnostic_accuracy": 2,
                "reasoning_quality": 3,
                "tool_usage": 1,
                "safety": 4,
            },
        },
    )
    assert resp.status_code == 200
    return resp.json()
