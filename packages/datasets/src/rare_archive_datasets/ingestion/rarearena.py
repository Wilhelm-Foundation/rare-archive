"""RareArena JSONL ingestion pipeline.

RareArena: ~50K rare disease diagnostic cases across 4K+ diseases.
Format: JSONL with clinical vignettes and diagnostic labels.
License: CC BY-NC-SA 4.0
Splits: RDS (Rare Disease Specialists), RDC (Rare Disease Cases)

Evaluation protocol: generate top-5 diagnoses -> GPT-4o scoring (0/1/2).
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

logger = logging.getLogger(__name__)


@dataclass
class RareArenaCase:
    """A single RareArena diagnostic case."""
    case_id: str
    clinical_vignette: str
    ground_truth_diagnosis: str
    disease_id: str | None = None
    disease_name: str | None = None
    hpo_terms: list[str] = field(default_factory=list)
    age_of_onset: str | None = None
    sex: str | None = None
    difficulty: str | None = None  # easy, medium, hard
    split: str | None = None  # rds, rdc
    patient_category: str | None = None  # assigned post-ingestion
    raw_data: dict[str, Any] = field(default_factory=dict)


def load_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    """Load a JSONL file, yielding one record per line."""
    with open(path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping line {line_num} in {path}: {e}")


def parse_case(record: dict[str, Any], split: str) -> RareArenaCase:
    """Parse a raw JSONL record into a RareArenaCase.

    Handles multiple RareArena format variants:
    - v1: {input, output, disease_id, ...}
    - v2: {clinical_note, diagnosis, orpha_code, ...}
    """
    case_id = (
        record.get("case_id")
        or record.get("id")
        or f"{split}_{hash(json.dumps(record, sort_keys=True)) % 10**8:08d}"
    )

    vignette = (
        record.get("clinical_vignette")
        or record.get("input")
        or record.get("clinical_note")
        or record.get("prompt")
        or ""
    )

    diagnosis = (
        record.get("ground_truth_diagnosis")
        or record.get("output")
        or record.get("diagnosis")
        or record.get("label")
        or ""
    )

    disease_id = (
        record.get("disease_id")
        or record.get("orpha_code")
        or record.get("omim_id")
        or record.get("mondo_id")
    )

    hpo_terms = record.get("hpo_terms", record.get("phenotypes", []))
    if isinstance(hpo_terms, str):
        hpo_terms = [t.strip() for t in hpo_terms.split(",")]

    return RareArenaCase(
        case_id=str(case_id),
        clinical_vignette=vignette,
        ground_truth_diagnosis=diagnosis,
        disease_id=disease_id,
        disease_name=record.get("disease_name"),
        hpo_terms=hpo_terms,
        age_of_onset=record.get("age_of_onset"),
        sex=record.get("sex"),
        difficulty=record.get("difficulty"),
        split=split,
        raw_data=record,
    )


def ingest_split(
    path: Path,
    split: str,
    max_cases: int | None = None,
) -> list[RareArenaCase]:
    """Ingest a RareArena JSONL split file.

    Args:
        path: Path to the JSONL file
        split: Split name ("rds" or "rdc")
        max_cases: Maximum cases to load (None = all)

    Returns:
        List of parsed RareArenaCase objects
    """
    cases = []
    for i, record in enumerate(load_jsonl(path)):
        if max_cases is not None and i >= max_cases:
            break
        cases.append(parse_case(record, split))

    logger.info(f"Ingested {len(cases)} cases from {path} (split={split})")
    return cases


def export_for_training(
    cases: list[RareArenaCase],
    output_path: Path,
    format: str = "chat",
) -> int:
    """Export cases as training-ready JSONL.

    Args:
        cases: List of RareArenaCase
        output_path: Output JSONL file path
        format: "chat" (OpenAI chat format) or "completion" (prompt/completion)

    Returns:
        Number of records written
    """
    count = 0
    with open(output_path, "w", encoding="utf-8") as f:
        for case in cases:
            if not case.clinical_vignette or not case.ground_truth_diagnosis:
                continue

            if format == "chat":
                record = {
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are an expert rare disease diagnostician. "
                                "Given a clinical vignette, provide your top differential "
                                "diagnoses with reasoning."
                            ),
                        },
                        {"role": "user", "content": case.clinical_vignette},
                        {
                            "role": "assistant",
                            "content": (
                                f"Based on the clinical presentation, my primary diagnosis is "
                                f"**{case.ground_truth_diagnosis}**."
                            ),
                        },
                    ],
                    "metadata": {
                        "case_id": case.case_id,
                        "split": case.split,
                        "disease_id": case.disease_id,
                        "patient_category": case.patient_category,
                    },
                }
            else:
                record = {
                    "prompt": case.clinical_vignette,
                    "completion": case.ground_truth_diagnosis,
                    "metadata": {
                        "case_id": case.case_id,
                        "split": case.split,
                    },
                }

            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1

    logger.info(f"Exported {count} records to {output_path}")
    return count


def compute_statistics(cases: list[RareArenaCase]) -> dict[str, Any]:
    """Compute dataset statistics."""
    diseases = set()
    disease_ids = set()
    hpo_counts: dict[str, int] = {}

    for case in cases:
        if case.ground_truth_diagnosis:
            diseases.add(case.ground_truth_diagnosis)
        if case.disease_id:
            disease_ids.add(case.disease_id)
        for hpo in case.hpo_terms:
            hpo_counts[hpo] = hpo_counts.get(hpo, 0) + 1

    return {
        "total_cases": len(cases),
        "unique_diseases": len(diseases),
        "unique_disease_ids": len(disease_ids),
        "unique_hpo_terms": len(hpo_counts),
        "cases_with_hpo": sum(1 for c in cases if c.hpo_terms),
        "cases_with_disease_id": sum(1 for c in cases if c.disease_id),
        "split_distribution": {
            split: sum(1 for c in cases if c.split == split)
            for split in set(c.split for c in cases if c.split)
        },
    }
