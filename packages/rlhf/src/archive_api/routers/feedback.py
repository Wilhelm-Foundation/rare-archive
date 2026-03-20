"""Clinical feedback endpoints — corrections, annotations, suggestions."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import ClinicalFeedback, Case, get_db

router = APIRouter()


class CorrectionSubmission(BaseModel):
    case_id: str
    expert_username: str
    corrected_diagnosis: str
    reasoning: str
    severity: str = "info"


class AnnotationSubmission(BaseModel):
    evaluation_id: int | None = None
    case_id: str | None = None
    expert_username: str
    feedback_type: str = Field(
        pattern="^(diagnostic_correction|clinical_note|tool_suggestion|safety_concern)$"
    )
    text: str
    severity: str = "info"


class FeedbackResponse(BaseModel):
    id: int
    case_id: str | None
    evaluation_id: int | None
    expert_username: str
    feedback_type: str
    corrected_diagnosis: str | None
    text: str | None
    severity: str


@router.post("/correction", response_model=FeedbackResponse)
async def submit_correction(
    submission: CorrectionSubmission,
    db: AsyncSession = Depends(get_db),
):
    """Submit a diagnostic correction for a case."""
    # Verify case exists
    result = await db.execute(
        select(Case).where(Case.case_id == submission.case_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Case not found")

    feedback = ClinicalFeedback(
        case_id=submission.case_id,
        expert_username=submission.expert_username,
        feedback_type="diagnostic_correction",
        corrected_diagnosis=submission.corrected_diagnosis,
        reasoning=submission.reasoning,
        text=f"Correction: {submission.corrected_diagnosis}. {submission.reasoning}",
        severity=submission.severity,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)

    return FeedbackResponse(
        id=feedback.id,
        case_id=feedback.case_id,
        evaluation_id=feedback.evaluation_id,
        expert_username=feedback.expert_username,
        feedback_type=feedback.feedback_type,
        corrected_diagnosis=feedback.corrected_diagnosis,
        text=feedback.text,
        severity=feedback.severity,
    )


@router.post("/annotation", response_model=FeedbackResponse)
async def submit_annotation(
    submission: AnnotationSubmission,
    db: AsyncSession = Depends(get_db),
):
    """Submit a free-text annotation."""
    feedback = ClinicalFeedback(
        case_id=submission.case_id,
        evaluation_id=submission.evaluation_id,
        expert_username=submission.expert_username,
        feedback_type=submission.feedback_type,
        text=submission.text,
        severity=submission.severity,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)

    return FeedbackResponse(
        id=feedback.id,
        case_id=feedback.case_id,
        evaluation_id=feedback.evaluation_id,
        expert_username=feedback.expert_username,
        feedback_type=feedback.feedback_type,
        corrected_diagnosis=feedback.corrected_diagnosis,
        text=feedback.text,
        severity=feedback.severity,
    )


@router.get("/corrections/{case_id}", response_model=list[FeedbackResponse])
async def get_corrections(
    case_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all corrections for a case."""
    result = await db.execute(
        select(ClinicalFeedback)
        .where(
            ClinicalFeedback.case_id == case_id,
            ClinicalFeedback.feedback_type == "diagnostic_correction",
        )
        .order_by(ClinicalFeedback.created_at.desc())
    )
    corrections = result.scalars().all()

    return [
        FeedbackResponse(
            id=f.id,
            case_id=f.case_id,
            evaluation_id=f.evaluation_id,
            expert_username=f.expert_username,
            feedback_type=f.feedback_type,
            corrected_diagnosis=f.corrected_diagnosis,
            text=f.text,
            severity=f.severity,
        )
        for f in corrections
    ]


@router.get("/stats")
async def feedback_stats(db: AsyncSession = Depends(get_db)):
    """Get feedback statistics."""
    total = await db.execute(select(func.count(ClinicalFeedback.id)))
    by_type = await db.execute(
        select(ClinicalFeedback.feedback_type, func.count(ClinicalFeedback.id))
        .group_by(ClinicalFeedback.feedback_type)
    )
    by_severity = await db.execute(
        select(ClinicalFeedback.severity, func.count(ClinicalFeedback.id))
        .group_by(ClinicalFeedback.severity)
    )

    return {
        "total_feedback": total.scalar(),
        "by_type": {t: c for t, c in by_type.all()},
        "by_severity": {s: c for s, c in by_severity.all()},
    }
