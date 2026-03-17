"""FAIR scoring for Rare AI Archive artifacts.

Extends Lattice Protocol's 16-criterion FAIR scoring with 6 Archive-specific
criteria. Total combined weight: 16.0 (11.2 base + 4.8 archive).
"""

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class FAIRCategory(str, Enum):
    FINDABLE = "findable"
    ACCESSIBLE = "accessible"
    INTEROPERABLE = "interoperable"
    REUSABLE = "reusable"


@dataclass
class FAIRResult:
    criterion_id: str
    name: str
    category: FAIRCategory
    weight: float
    passed: bool
    message: str


def score_artifact(metadata: dict[str, Any]) -> dict[str, Any]:
    """Score an Archive artifact against combined FAIR criteria.

    Returns a dict with:
    - total_score: weighted score (0-100)
    - max_score: maximum possible score
    - results: list of FAIRResult dicts
    - by_category: scores per FAIR category
    - publication_ready: bool (all required criteria pass)
    """
    results = []

    # --- Base Lattice Protocol criteria (subset we can check from metadata) ---

    # F2: Rich Metadata
    has_rich = all(
        metadata.get(f) for f in ["name", "description", "version"]
    )
    results.append(FAIRResult("F2", "Rich Metadata", FAIRCategory.FINDABLE, 0.8, has_rich,
                              "name, description, version present" if has_rich else "Missing name/description/version"))

    # F4: Semantic Tags
    keywords = metadata.get("keywords", metadata.get("tags", []))
    has_tags = len(keywords) >= 3
    results.append(FAIRResult("F4", "Semantic Tags", FAIRCategory.FINDABLE, 0.4, has_tags,
                              f"{len(keywords)} keywords" if has_tags else "Need 3+ keywords"))

    # F1: Persistent Identifier
    has_pid = bool(metadata.get("persistent_id"))
    results.append(FAIRResult("F1", "Persistent Identifier", FAIRCategory.FINDABLE, 1.0, has_pid,
                              "persistent_id present" if has_pid else "No persistent_id"))

    # R1: SPDX License
    has_license = bool(metadata.get("license"))
    results.append(FAIRResult("R1", "SPDX License", FAIRCategory.REUSABLE, 1.0, has_license,
                              f"license: {metadata.get('license')}" if has_license else "No license"))

    # R2: Provenance
    has_provenance = bool(metadata.get("creators"))
    results.append(FAIRResult("R2", "Provenance", FAIRCategory.REUSABLE, 0.8, has_provenance,
                              "creators listed" if has_provenance else "No creators"))

    # I3: References
    has_refs = bool(metadata.get("references"))
    results.append(FAIRResult("I3", "References", FAIRCategory.INTEROPERABLE, 0.4, has_refs,
                              "cross-references present" if has_refs else "No references"))

    # --- Archive-specific criteria ---

    # RA-F1: Ontology Grounding
    has_grounding = any(
        metadata.get(k) for k in ["category_id", "tool_id", "patient_category", "patient_categories"]
    )
    results.append(FAIRResult("RA-F1", "Ontology Grounding", FAIRCategory.FINDABLE, 0.8, has_grounding,
                              "ontology reference found" if has_grounding else "No ontology grounding"))

    # RA-I1: aDNA Envelope Valid
    adna = metadata.get("adna", {})
    has_adna = all(adna.get(f) for f in ["type", "namespace", "triad"]) if adna else False
    results.append(FAIRResult("RA-I1", "aDNA Envelope Valid", FAIRCategory.INTEROPERABLE, 1.0, has_adna,
                              "valid aDNA envelope" if has_adna else "Missing/invalid aDNA envelope"))

    # RA-R1: PHI Governance
    artifact_type = metadata.get("adna", {}).get("type", "")
    if "dataset" in artifact_type:
        phi = metadata.get("consent", {}).get("phi_status") or metadata.get("phi_status")
        has_phi = bool(phi)
        results.append(FAIRResult("RA-R1", "PHI Governance", FAIRCategory.REUSABLE, 1.0, has_phi,
                                  f"phi_status: {phi}" if has_phi else "No PHI status declared"))
    else:
        results.append(FAIRResult("RA-R1", "PHI Governance", FAIRCategory.REUSABLE, 1.0, True,
                                  "N/A (non-dataset artifact)"))

    # RA-R2: Training Provenance (for models)
    if "model" in artifact_type:
        lineage = metadata.get("lineage", {})
        has_lineage = bool(lineage.get("parent_model_id") or lineage.get("training_run_id"))
        results.append(FAIRResult("RA-R2", "Training Provenance", FAIRCategory.REUSABLE, 0.8, has_lineage,
                                  "training lineage present" if has_lineage else "No training lineage"))
    else:
        results.append(FAIRResult("RA-R2", "Training Provenance", FAIRCategory.REUSABLE, 0.8, True,
                                  "N/A (non-model artifact)"))

    # Compute scores
    total_weight = sum(r.weight for r in results)
    earned_weight = sum(r.weight for r in results if r.passed)
    score = (earned_weight / total_weight * 100) if total_weight > 0 else 0

    # Check publication readiness
    required_ids = {"F2", "R1", "RA-F1", "RA-I1", "RA-R1"}
    required_pass = all(
        r.passed for r in results if r.criterion_id in required_ids
    )

    # Scores by category
    by_category = {}
    for cat in FAIRCategory:
        cat_results = [r for r in results if r.category == cat]
        cat_total = sum(r.weight for r in cat_results)
        cat_earned = sum(r.weight for r in cat_results if r.passed)
        by_category[cat.value] = {
            "score": (cat_earned / cat_total * 100) if cat_total > 0 else 0,
            "earned": cat_earned,
            "total": cat_total,
        }

    return {
        "total_score": round(score, 1),
        "max_score": 100,
        "earned_weight": round(earned_weight, 1),
        "total_weight": round(total_weight, 1),
        "publication_ready": required_pass,
        "results": [
            {
                "id": r.criterion_id,
                "name": r.name,
                "category": r.category.value,
                "weight": r.weight,
                "passed": r.passed,
                "message": r.message,
            }
            for r in results
        ],
        "by_category": by_category,
    }
