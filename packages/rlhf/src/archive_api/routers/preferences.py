"""Preference pair extraction and HuggingFace export."""

import json
import logging
import os
from pathlib import Path
from shutil import copy2
from tempfile import TemporaryDirectory

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import verify_api_key
from ..config import settings
from ..models.database import Evaluation, PreferenceExport, get_db

logger = logging.getLogger(__name__)

router = APIRouter()

# Stable path in HF repo — one canonical file that grows via append
HF_PREFERENCES_PATH = "data/preferences.jsonl"

# Local persistent cache for dedup when HF token is unavailable
LOCAL_EXPORT_DIR = Path(os.getenv("DATA_DIR", "/data/latlab/rare-archive")) / "exports"
LOCAL_PREFERENCES_PATH = LOCAL_EXPORT_DIR / "preferences.jsonl"


def _load_existing_ids(jsonl_path: Path) -> set[int]:
    """Load evaluation_ids already present in a JSONL file."""
    ids: set[int] = set()
    if not jsonl_path.exists():
        return ids
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                eid = record.get("metadata", {}).get("evaluation_id")
                if eid is not None:
                    ids.add(int(eid))
            except (json.JSONDecodeError, ValueError):
                continue
    return ids


def _download_existing(tmpdir: Path) -> Path:
    """Load existing preferences JSONL for deduplication.

    Checks local persistent cache first, then HuggingFace if token is set.
    Returns a path in tmpdir (may be empty/nonexistent on first export).
    """
    local_path = tmpdir / "existing_preferences.jsonl"

    # Check local persistent cache first
    if LOCAL_PREFERENCES_PATH.exists():
        copy2(LOCAL_PREFERENCES_PATH, local_path)
        logger.debug(f"Loaded {local_path.stat().st_size} bytes from local cache")
        return local_path

    # Try HuggingFace if token is available
    if settings.hf_token:
        try:
            from huggingface_hub import hf_hub_download
            downloaded = hf_hub_download(
                repo_id=f"{settings.hf_org}/{settings.hf_dataset}",
                filename=HF_PREFERENCES_PATH,
                repo_type="dataset",
                token=settings.hf_token,
                local_dir=str(tmpdir),
                local_dir_use_symlinks=False,
            )
            downloaded_path = Path(downloaded)
            if downloaded_path != local_path and downloaded_path.exists():
                downloaded_path.rename(local_path)
            return local_path
        except Exception:
            logger.debug("No existing preferences file on HuggingFace (first export)")

    return local_path


@router.get("/pairs")
async def get_preference_pairs(
    patient_category: str | None = None,
    limit: int = 1000,
    _key: str = Depends(verify_api_key),
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
    append_only: bool = True,
    _key: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Export preference pairs to HuggingFace dataset.

    With append_only=True (default), downloads existing data from HF,
    deduplicates by evaluation_id, and appends only new pairs.
    """
    pairs_response = await get_preference_pairs(patient_category, limit=10000, db=db)
    pairs = pairs_response["pairs"]

    if not pairs:
        return {"status": "no_data", "message": "No preference pairs to export"}

    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Determine which pairs are new
        existing_ids: set[int] = set()
        existing_path = tmpdir_path / "existing_preferences.jsonl"

        if append_only:
            existing_path = _download_existing(tmpdir_path)
            existing_ids = _load_existing_ids(existing_path)

        new_pairs = [
            p for p in pairs
            if p["metadata"]["evaluation_id"] not in existing_ids
        ]

        if not new_pairs and append_only:
            return {
                "status": "no_new_data",
                "message": f"All {len(pairs)} pairs already exported",
                "existing_count": len(existing_ids),
            }

        # Build merged file: existing lines + new pairs
        merged_path = tmpdir_path / "preferences.jsonl"
        with open(merged_path, "w") as out:
            # Copy existing lines verbatim
            if existing_path.exists():
                with open(existing_path) as existing:
                    for line in existing:
                        out.write(line)
            # Append new pairs
            for pair in new_pairs:
                out.write(json.dumps(pair, ensure_ascii=False) + "\n")

        # Save local cache for future dedup
        LOCAL_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        copy2(merged_path, LOCAL_PREFERENCES_PATH)

        # Upload to HuggingFace
        commit_hash = ""
        pairs_to_report = new_pairs if append_only else pairs
        if settings.hf_token:
            try:
                from huggingface_hub import HfApi
                api = HfApi(token=settings.hf_token)

                api.upload_file(
                    path_or_fileobj=str(merged_path),
                    path_in_repo=HF_PREFERENCES_PATH,
                    repo_id=f"{settings.hf_org}/{settings.hf_dataset}",
                    repo_type="dataset",
                )
                commit_hash = "uploaded"
                logger.info(
                    f"Exported {len(pairs_to_report)} new preference pairs "
                    f"(total: {len(existing_ids) + len(new_pairs)}) to HuggingFace"
                )
            except Exception as e:
                logger.error(f"HuggingFace export failed: {e}")
                export = PreferenceExport(
                    evaluation_count=len(pairs_to_report),
                    hf_dataset_id=f"{settings.hf_org}/{settings.hf_dataset}",
                    status="failed",
                )
                db.add(export)
                await db.commit()
                return {"status": "failed", "error": str(e)}

        # Record export
        export = PreferenceExport(
            evaluation_count=len(pairs_to_report),
            hf_dataset_id=f"{settings.hf_org}/{settings.hf_dataset}",
            hf_commit_hash=commit_hash,
            status="success",
        )
        db.add(export)
        await db.commit()

    return {
        "status": "success",
        "new_pairs_exported": len(new_pairs),
        "existing_pairs": len(existing_ids),
        "total_pairs": len(existing_ids) + len(new_pairs),
        "hf_dataset": f"{settings.hf_org}/{settings.hf_dataset}",
    }
