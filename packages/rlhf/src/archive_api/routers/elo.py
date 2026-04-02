"""ELO rating endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import verify_api_key
from ..config import settings
from ..models.database import ModelRating, get_db

router = APIRouter()


class ELORatingResponse(BaseModel):
    model_id: str
    patient_category: str
    overall_elo: float
    diagnostic_accuracy_elo: float
    reasoning_quality_elo: float
    tool_usage_elo: float
    safety_elo: float
    total_comparisons: int
    wins: int
    losses: int
    ties: int


class ELOUpdateRequest(BaseModel):
    winner_model_id: str
    loser_model_id: str
    patient_category: str = "general"
    evaluation_mode: str = "arena"
    is_tie: bool = False
    annotations: dict | None = None


def _compute_elo_change(rating_a: float, rating_b: float, score_a: float, k: float) -> tuple[float, float]:
    """Compute ELO rating changes.

    Args:
        rating_a: Current rating of player A
        rating_b: Current rating of player B
        score_a: Actual score (1.0=win, 0.5=tie, 0.0=loss)
        k: K-factor

    Returns:
        (new_rating_a, new_rating_b)
    """
    expected_a = 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400))
    expected_b = 1.0 - expected_a

    new_a = rating_a + k * (score_a - expected_a)
    new_b = rating_b + k * ((1.0 - score_a) - expected_b)

    return new_a, new_b


@router.get("/ratings", response_model=list[ELORatingResponse])
async def get_ratings(
    patient_category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get all model ratings, optionally filtered by patient category."""
    query = select(ModelRating)
    if patient_category:
        query = query.where(ModelRating.patient_category == patient_category)
    query = query.order_by(ModelRating.overall_elo.desc())

    result = await db.execute(query)
    ratings = result.scalars().all()

    return [
        ELORatingResponse(
            model_id=r.model_id,
            patient_category=r.patient_category,
            overall_elo=r.overall_elo,
            diagnostic_accuracy_elo=r.diagnostic_accuracy_elo,
            reasoning_quality_elo=r.reasoning_quality_elo,
            tool_usage_elo=r.tool_usage_elo,
            safety_elo=r.safety_elo,
            total_comparisons=r.total_comparisons,
            wins=r.wins,
            losses=r.losses,
            ties=r.ties,
        )
        for r in ratings
    ]


@router.get("/ratings/{model_id}", response_model=list[ELORatingResponse])
async def get_model_ratings(
    model_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all ratings for a specific model (across categories)."""
    result = await db.execute(
        select(ModelRating).where(ModelRating.model_id == model_id)
    )
    ratings = result.scalars().all()
    if not ratings:
        raise HTTPException(status_code=404, detail=f"No ratings found for model {model_id}")

    return [
        ELORatingResponse(
            model_id=r.model_id,
            patient_category=r.patient_category,
            overall_elo=r.overall_elo,
            diagnostic_accuracy_elo=r.diagnostic_accuracy_elo,
            reasoning_quality_elo=r.reasoning_quality_elo,
            tool_usage_elo=r.tool_usage_elo,
            safety_elo=r.safety_elo,
            total_comparisons=r.total_comparisons,
            wins=r.wins,
            losses=r.losses,
            ties=r.ties,
        )
        for r in ratings
    ]


async def compute_elo_update(request: ELOUpdateRequest, db: AsyncSession) -> dict:
    """Core ELO update logic — callable from both the route and evaluations."""
    k = settings.elo_k_factor
    cat = request.patient_category
    mode = request.evaluation_mode

    # Get or create ratings for both models
    async def get_or_create_rating(model_id: str) -> ModelRating:
        result = await db.execute(
            select(ModelRating).where(
                ModelRating.model_id == model_id,
                ModelRating.patient_category == cat,
                ModelRating.evaluation_mode == mode,
            )
        )
        rating = result.scalar_one_or_none()
        if not rating:
            rating = ModelRating(
                model_id=model_id,
                patient_category=cat,
                evaluation_mode=mode,
                overall_elo=settings.elo_initial_rating,
                diagnostic_accuracy_elo=settings.elo_initial_rating,
                reasoning_quality_elo=settings.elo_initial_rating,
                tool_usage_elo=settings.elo_initial_rating,
                safety_elo=settings.elo_initial_rating,
                total_comparisons=0,
                wins=0,
                losses=0,
                ties=0,
            )
            db.add(rating)
        return rating

    winner = await get_or_create_rating(request.winner_model_id)
    loser = await get_or_create_rating(request.loser_model_id)

    score = 0.5 if request.is_tie else 1.0

    # Update overall ELO
    winner.overall_elo, loser.overall_elo = _compute_elo_change(
        winner.overall_elo, loser.overall_elo, score, k
    )

    # Update dimensional ELOs if annotations provided
    if request.annotations:
        dims = ["diagnostic_accuracy", "reasoning_quality", "tool_usage", "safety"]
        for dim in dims:
            w_score = request.annotations.get(f"winner_{dim}", 0)
            l_score = request.annotations.get(f"loser_{dim}", 0)

            if w_score > 0 or l_score > 0:
                dim_score = 1.0 if w_score > l_score else (0.5 if w_score == l_score else 0.0)
                w_elo = getattr(winner, f"{dim}_elo")
                l_elo = getattr(loser, f"{dim}_elo")
                new_w, new_l = _compute_elo_change(w_elo, l_elo, dim_score, k)
                setattr(winner, f"{dim}_elo", new_w)
                setattr(loser, f"{dim}_elo", new_l)

    # Update counters
    winner.total_comparisons += 1
    loser.total_comparisons += 1

    if request.is_tie:
        winner.ties += 1
        loser.ties += 1
    else:
        winner.wins += 1
        loser.losses += 1

    await db.commit()

    return {
        "status": "updated",
        "winner": {"model_id": winner.model_id, "new_elo": round(winner.overall_elo, 1)},
        "loser": {"model_id": loser.model_id, "new_elo": round(loser.overall_elo, 1)},
    }


@router.post("/update")
async def update_elo(
    request: ELOUpdateRequest,
    _key: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Update ELO ratings after a comparison."""
    return await compute_elo_update(request, db)
