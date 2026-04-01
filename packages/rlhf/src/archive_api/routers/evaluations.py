"""Evaluation submission endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import verify_api_key
from ..models.database import Evaluation, Expert, get_db

router = APIRouter()


class AnnotationScores(BaseModel):
    diagnostic_accuracy: int = Field(ge=0, le=5)
    reasoning_quality: int = Field(ge=0, le=5)
    tool_usage: int = Field(ge=0, le=5)
    safety: int = Field(ge=0, le=5)


class EvaluationSubmission(BaseModel):
    expert_username: str
    case_id: str
    patient_category: str = "general"
    model_a_id: str
    model_b_id: str
    model_a_response: str
    model_b_response: str
    winner: str = Field(pattern="^(a|b|tie)$")
    model_a_annotations: AnnotationScores
    model_b_annotations: AnnotationScores


class EvaluationResponse(BaseModel):
    id: int
    case_id: str
    winner: str
    elo_update: dict


@router.post("/submit", response_model=EvaluationResponse)
async def submit_evaluation(
    submission: EvaluationSubmission,
    _key: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Submit an Arena evaluation with structured annotations."""
    # Verify expert exists
    result = await db.execute(
        select(Expert).where(Expert.username == submission.expert_username)
    )
    expert = result.scalar_one_or_none()
    if not expert:
        raise HTTPException(status_code=404, detail="Expert not found")

    evaluation = Evaluation(
        expert_id=expert.id,
        case_id=submission.case_id,
        patient_category=submission.patient_category,
        model_a_id=submission.model_a_id,
        model_b_id=submission.model_b_id,
        model_a_response=submission.model_a_response,
        model_b_response=submission.model_b_response,
        winner=submission.winner,
        annotations={
            "model_a": submission.model_a_annotations.model_dump(),
            "model_b": submission.model_b_annotations.model_dump(),
        },
    )
    db.add(evaluation)
    await db.commit()
    await db.refresh(evaluation)

    # Trigger ELO update
    from .elo import update_elo, ELOUpdateRequest

    winner_id = submission.model_a_id if submission.winner == "a" else submission.model_b_id
    loser_id = submission.model_b_id if submission.winner == "a" else submission.model_a_id

    w_ann = submission.model_a_annotations if submission.winner == "a" else submission.model_b_annotations
    l_ann = submission.model_b_annotations if submission.winner == "a" else submission.model_a_annotations

    elo_req = ELOUpdateRequest(
        winner_model_id=winner_id,
        loser_model_id=loser_id,
        patient_category=submission.patient_category,
        is_tie=(submission.winner == "tie"),
        annotations={
            f"winner_{k}": v for k, v in w_ann.model_dump().items()
        } | {
            f"loser_{k}": v for k, v in l_ann.model_dump().items()
        },
    )
    elo_result = await update_elo(elo_req, db)

    return EvaluationResponse(
        id=evaluation.id,
        case_id=evaluation.case_id,
        winner=evaluation.winner,
        elo_update=elo_result,
    )


@router.get("/stats")
async def evaluation_stats(db: AsyncSession = Depends(get_db)):
    """Get evaluation statistics."""
    total = await db.execute(select(func.count(Evaluation.id)))
    by_category = await db.execute(
        select(Evaluation.patient_category, func.count(Evaluation.id))
        .group_by(Evaluation.patient_category)
    )

    return {
        "total_evaluations": total.scalar(),
        "by_category": {
            cat: count for cat, count in by_category.all()
        },
    }
