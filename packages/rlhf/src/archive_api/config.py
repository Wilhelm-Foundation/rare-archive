"""Configuration for the Archive API."""

import os
from dataclasses import dataclass


@dataclass
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "")
    redis_url: str = os.getenv("REDIS_URL", "")
    openwebui_url: str = os.getenv("OPENWEBUI_URL", "http://localhost:3000")

    def __post_init__(self):
        if not self.database_url:
            raise ValueError(
                "DATABASE_URL environment variable must be set. "
                "Example: postgresql+asyncpg://user:pass@host:5432/dbname"
            )
    hf_token: str = os.getenv("HF_TOKEN", "")
    hf_org: str = os.getenv("HF_ORG", "wilhelm-foundation")
    hf_dataset: str = os.getenv("HF_DATASET", "rare-archive-rlhf-preferences")

    # ChromaDB (container-to-container on lattice-l2 network)
    chromadb_url: str = os.getenv("CHROMADB_URL", "http://rare-archive-chromadb:8000")

    # ELO settings
    elo_k_factor: float = float(os.getenv("ELO_K_FACTOR", "32"))
    elo_initial_rating: float = float(os.getenv("ELO_INITIAL_RATING", "1500"))


settings = Settings()
