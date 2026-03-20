"""Database models and initialization."""

from datetime import datetime

from sqlalchemy import (
    Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text,
    UniqueConstraint, create_engine,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from ..config import settings


class Base(DeclarativeBase):
    pass


class Expert(Base):
    """Registered clinical expert."""
    __tablename__ = "experts"

    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    display_name = Column(String(255))
    email = Column(String(255))
    subspecialty = Column(String(255))
    institution = Column(String(255))
    years_experience = Column(Integer)
    patient_categories = Column(JSON, default=list)  # list of category_ids
    registered_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)

    evaluations = relationship("Evaluation", back_populates="expert")


class ModelRating(Base):
    """Multi-dimensional ELO rating for a model."""
    __tablename__ = "model_ratings"

    id = Column(Integer, primary_key=True)
    model_id = Column(String(255), nullable=False)
    patient_category = Column(String(255), nullable=False, default="general")
    evaluation_mode = Column(String(50), nullable=False, default="arena")

    # Multi-dimensional ratings
    overall_elo = Column(Float, default=1500.0)
    diagnostic_accuracy_elo = Column(Float, default=1500.0)
    reasoning_quality_elo = Column(Float, default=1500.0)
    tool_usage_elo = Column(Float, default=1500.0)
    safety_elo = Column(Float, default=1500.0)

    total_comparisons = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    ties = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("model_id", "patient_category", "evaluation_mode",
                         name="uq_model_category_mode"),
    )


class Evaluation(Base):
    """A single Arena evaluation (comparison of two models)."""
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True)
    expert_id = Column(Integer, ForeignKey("experts.id"), nullable=False)
    case_id = Column(String(255), nullable=False)
    patient_category = Column(String(255))

    model_a_id = Column(String(255), nullable=False)
    model_b_id = Column(String(255), nullable=False)
    model_a_response = Column(Text)
    model_b_response = Column(Text)

    winner = Column(String(10))  # "a", "b", "tie"

    # Structured annotations (0-5 each, for both models)
    annotations = Column(JSON)
    # {
    #   "model_a": {"diagnostic_accuracy": 4, "reasoning_quality": 3, ...},
    #   "model_b": {"diagnostic_accuracy": 2, "reasoning_quality": 4, ...}
    # }

    created_at = Column(DateTime, default=datetime.utcnow)

    expert = relationship("Expert", back_populates="evaluations")


class Case(Base):
    """Clinical case for arena evaluation."""
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True)
    case_id = Column(String(255), unique=True, nullable=False)
    category = Column(String(255), nullable=False, default="general")
    vignette = Column(Text, nullable=False)
    known_diagnosis = Column(String(500))
    difficulty = Column(String(50), default="medium")  # easy, medium, hard
    source = Column(String(255))  # e.g. "combined_eval", "synthetic", "expert_submitted"
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


class ClinicalFeedback(Base):
    """Clinician feedback: corrections, annotations, suggestions."""
    __tablename__ = "clinical_feedback"

    id = Column(Integer, primary_key=True)
    case_id = Column(String(255), ForeignKey("cases.case_id"), nullable=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id"), nullable=True)
    expert_username = Column(String(255), nullable=False)

    feedback_type = Column(String(50), nullable=False)
    # diagnostic_correction | clinical_note | tool_suggestion | safety_concern

    corrected_diagnosis = Column(String(500))
    reasoning = Column(Text)
    text = Column(Text)
    severity = Column(String(50), default="info")  # info, warning, critical

    created_at = Column(DateTime, default=datetime.utcnow)


class PreferenceExport(Base):
    """Track preference data exports to HuggingFace."""
    __tablename__ = "preference_exports"

    id = Column(Integer, primary_key=True)
    export_date = Column(DateTime, default=datetime.utcnow)
    evaluation_count = Column(Integer)
    hf_dataset_id = Column(String(255))
    hf_commit_hash = Column(String(64))
    status = Column(String(50), default="pending")  # pending, success, failed


# Async engine and session
engine = create_async_engine(settings.database_url, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Get database session."""
    async with async_session() as session:
        yield session
