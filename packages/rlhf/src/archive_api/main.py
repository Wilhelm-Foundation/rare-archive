"""Archive API — FastAPI application.

Multi-dimensional ELO tracking, expert matching, and preference export
for the Rare AI Archive RLHF system.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import elo, experts, evaluations, preferences


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    # Startup: initialize database tables
    from .models.database import init_db
    await init_db()
    yield
    # Shutdown: cleanup


app = FastAPI(
    title="Rare AI Archive API",
    description="Multi-dimensional ELO tracking and RLHF preference export",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(elo.router, prefix="/elo", tags=["ELO"])
app.include_router(experts.router, prefix="/experts", tags=["Experts"])
app.include_router(evaluations.router, prefix="/evaluations", tags=["Evaluations"])
app.include_router(preferences.router, prefix="/preferences", tags=["Preferences"])


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "rare-archive-api"}
