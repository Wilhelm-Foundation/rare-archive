"""Preference pair extraction and HuggingFace export."""

import json
import logging
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.database import Evaluation, PreferenceExport, get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/pairs")
async def get_preference_pairs(
    patient_category: str | None = None,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db),
):
    """Extract DPO-compatible preference pairs from evaluations."""
    query = select(Evaluation)
    if patient_category:
        query = query.where(Evaluation.patient_category == patient_category)
    query = query.order_by(Evaluation.created_at.desc()).limit(limit)

    result = await db.execute(query)
    evaluations = result.scalars().all()

    pairs = []
    for eval in evaluations:
        if eval.winner == "tie":
            continue  # Skip ties for DPO

        chosen_response = eval.model_a_response if eval.winner == "a" else eval.model_b_response
        rejected_response = eval.model_b_response if eval.winner == "a" else eval.model_a_response

        pairs.append({
            "prompt": f"Case {eval.case_id}",  # Full vignette would come from case library
            "chosen": chosen_response,
            "rejected": rejected_response,
            "metadata": {
                "evaluation_id": eval.id,
                "expert_id": eval.expert_id,
                "patient_category": eval.patient_category,
                "winner_model": eval.model_a_id if eval.winner == "a" else eval.model_b_id,
                "loser_model": eval.model_b_id if eval.winner == "a" else eval.model_a_id,
                "annotations": eval.annotations,
            },
        })

    return {"count": len(pairs), "pairs": pairs}


@router.post("/export")
async def export_to_huggingface(
    patient_category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Export preference pairs to HuggingFace dataset."""
    # Get pairs
    pairs_response = await get_preference_pairs(patient_category, limit=10000, db=db)
    pairs = pairs_response["pairs"]

    if not pairs:
        return {"status": "no_data", "message": "No preference pairs to export"}

    with TemporaryDirectory() as tmpdir:
        # Write JSONL
        jsonl_path = Path(tmpdir) / "preferences.jsonl"
        with open(jsonl_path, "w") as f:
            for pair in pairs:
                f.write(json.dumps(pair, ensure_ascii=False) + "\n")

        # Upload to HuggingFace
        commit_hash = ""
        if settings.hf_token:
            try:
                from huggingface_hub import HfApi
                api = HfApi(token=settings.hf_token)

                api.upload_file(
                    path_or_fileobj=str(jsonl_path),
                    path_in_repo=f"data/preferences_{datetime.utcnow().strftime('%Y%m%d')}.jsonl",
                    repo_id=f"{settings.hf_org}/{settings.hf_dataset}",
                    repo_type="dataset",
                )
                commit_hash = "uploaded"
                logger.info(f"Exported {len(pairs)} preference pairs to HuggingFace")
            except Exception as e:
                logger.error(f"HuggingFace export failed: {e}")
                export = PreferenceExport(
                    evaluation_count=len(pairs),
                    hf_dataset_id=f"{settings.hf_org}/{settings.hf_dataset}",
                    status="failed",
                )
                db.add(export)
                await db.commit()
                return {"status": "failed", "error": str(e)}

        # Record export
        export = PreferenceExport(
            evaluation_count=len(pairs),
            hf_dataset_id=f"{settings.hf_org}/{settings.hf_dataset}",
            hf_commit_hash=commit_hash,
            status="success",
        )
        db.add(export)
        await db.commit()

    return {
        "status": "success",
        "pairs_exported": len(pairs),
        "hf_dataset": f"{settings.hf_org}/{settings.hf_dataset}",
    }
