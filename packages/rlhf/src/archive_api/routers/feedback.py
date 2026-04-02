"""Clinical feedback endpoints — corrections, annotations, suggestions."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import verify_api_key
from ..integrations.chromadb import store_correction, search_corrections
from ..models.database import ClinicalFeedback, Case, get_db

logger = logging.getLogger(__name__)

router = APIRouter()

SYSTEM_PROMPT = (
    "You are an expert rare disease diagnostician. Provide a precise diagnosis "
    "with differential reasoning, citing relevant clinical features and "
    "genetic/biochemical markers."
)


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
        pattern="^(diagnostic_correction|clinical_note|tool_suggestion|safety_concern|tool_quality)$"
    )
    text: str
    severity: str = "info"


class ToolQualitySubmission(BaseModel):
    evaluation_id: int | None = None
    case_id: str | None = None
    expert_username: str
    tool_name: str
    quality_score: int = Field(ge=0, le=5)
    was_appropriate: bool
    was_missing: bool
    reasoning: str


class FeedbackResponse(BaseModel):
    id: int
    case_id: str | None
    evaluation_id: int | None
    expert_username: str
    feedback_type: str
    corrected_diagnosis: str | None
    text: str | None
    severity: str
    structured_data: dict | None = None


class CorrectionSearchResult(BaseModel):
    id: str
    document: str
    metadata: dict
    distance: float | None


@router.post("/correction", response_model=FeedbackResponse)
async def submit_correction(
    submission: CorrectionSubmission,
    _key: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Submit a diagnostic correction for a case.

    Stores in PostgreSQL (primary) and ChromaDB (embeddings for RAG retrieval).
    """
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

    # Store in ChromaDB for RAG retrieval (best-effort, don't fail the request)
    try:
        await store_correction(
            case_id=submission.case_id,
            correction_text=f"{submission.corrected_diagnosis}. {submission.reasoning}",
            metadata={
                "expert": submission.expert_username,
                "severity": submission.severity,
                "corrected_diagnosis": submission.corrected_diagnosis,
                "feedback_id": feedback.id,
            },
        )
    except Exception as e:
        logger.warning(f"ChromaDB store failed (non-fatal): {e}")

    return FeedbackResponse(
        id=feedback.id,
        case_id=feedback.case_id,
        evaluation_id=feedback.evaluation_id,
        expert_username=feedback.expert_username,
        feedback_type=feedback.feedback_type,
        corrected_diagnosis=feedback.corrected_diagnosis,
        text=feedback.text,
        severity=feedback.severity,
        structured_data=feedback.structured_data,
    )


@router.post("/tool-quality", response_model=FeedbackResponse)
async def submit_tool_quality(
    submission: ToolQualitySubmission,
    _key: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Submit structured feedback on tool-usage quality."""
    feedback = ClinicalFeedback(
        case_id=submission.case_id,
        evaluation_id=submission.evaluation_id,
        expert_username=submission.expert_username,
        feedback_type="tool_quality",
        text=submission.reasoning,
        severity="info",
        structured_data={
            "tool_name": submission.tool_name,
            "quality_score": submission.quality_score,
            "was_appropriate": submission.was_appropriate,
            "was_missing": submission.was_missing,
        },
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
        structured_data=feedback.structured_data,
    )


@router.post("/annotation", response_model=FeedbackResponse)
async def submit_annotation(
    submission: AnnotationSubmission,
    _key: str = Depends(verify_api_key),
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
        structured_data=feedback.structured_data,
    )


@router.get("/corrections/search")
async def search_correction_embeddings(
    query: str,
    n_results: int = 5,
):
    """Search corrections by semantic similarity via ChromaDB embeddings."""
    results = await search_corrections(query_text=query, n_results=n_results)
    return {"query": query, "count": len(results), "results": results}


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
            structured_data=f.structured_data,
        )
        for f in corrections
    ]


@router.get("/export-training")
async def export_training_data(
    _key: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Export corrections as SFT-compatible JSONL for training.

    Joins corrections with case vignettes to produce chat-format training data:
    system + user (vignette) + assistant (corrected diagnosis + reasoning).
    """
    result = await db.execute(
        select(ClinicalFeedback, Case)
        .join(Case, ClinicalFeedback.case_id == Case.case_id)
        .where(ClinicalFeedback.feedback_type == "diagnostic_correction")
        .order_by(ClinicalFeedback.created_at)
    )
    rows = result.all()

    if not rows:
        return {"status": "no_data", "message": "No corrections to export"}

    def generate_jsonl():
        for feedback, case in rows:
            record = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": case.vignette},
                    {
                        "role": "assistant",
                        "content": (
                            f"**{feedback.corrected_diagnosis}**\n\n"
                            f"{feedback.reasoning}"
                        ),
                    },
                ],
                "metadata": {
                    "source": "clinical_correction",
                    "expert": feedback.expert_username,
                    "case_id": feedback.case_id,
                    "severity": feedback.severity,
                },
            }
            yield json.dumps(record, ensure_ascii=False) + "\n"

    return StreamingResponse(
        generate_jsonl(),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": "attachment; filename=corrections_sft.jsonl"},
    )


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
