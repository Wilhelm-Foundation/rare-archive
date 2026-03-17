"""Maps RareArena cases to patient categories from the ontology.

This module bridges the datasets repo and the ontology repo,
assigning each case to its most appropriate patient category.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rare_archive_datasets.ingestion.rarearena import RareArenaCase

logger = logging.getLogger(__name__)


@dataclass
class CategoryMapping:
    """Result of mapping a case to a patient category."""
    case_id: str
    category_id: str | None
    match_method: str  # "disease_id", "phenotype_overlap", "unmatched"
    confidence: float  # 0.0 - 1.0
    candidate_categories: list[tuple[str, float]]  # (category_id, score)


def load_category_index(categories_dir: Path) -> dict[str, dict]:
    """Load patient categories and build lookup indices.

    Returns a dict with:
    - categories: list of category dicts
    - disease_index: {disease_id: category_id}
    - phenotype_index: {hpo_id: [category_id, ...]}
    """
    categories = []
    disease_index: dict[str, str] = {}
    phenotype_index: dict[str, list[str]] = {}

    for f in sorted(categories_dir.glob("*.json")):
        with open(f) as fh:
            cat = json.load(fh)
            categories.append(cat)

            cat_id = cat["category_id"]

            # Index diseases
            for disease in cat.get("diseases", []):
                for key in ["disease_id", "ordo_id", "omim_id", "mondo_id", "gard_id"]:
                    val = disease.get(key)
                    if val:
                        disease_index[val] = cat_id

            # Index phenotypes
            for pheno in cat.get("phenotypic_features", []):
                hpo_id = pheno.get("hpo_id")
                if hpo_id:
                    phenotype_index.setdefault(hpo_id, []).append(cat_id)

    return {
        "categories": categories,
        "disease_index": disease_index,
        "phenotype_index": phenotype_index,
    }


def map_case(
    case: RareArenaCase,
    index: dict[str, Any],
    min_phenotype_overlap: float = 0.2,
) -> CategoryMapping:
    """Map a single case to a patient category.

    Priority:
    1. Exact disease ID match
    2. Phenotype overlap (Jaccard similarity)
    3. Unmatched
    """
    # Try disease ID match
    if case.disease_id and case.disease_id in index["disease_index"]:
        cat_id = index["disease_index"][case.disease_id]
        return CategoryMapping(
            case_id=case.case_id,
            category_id=cat_id,
            match_method="disease_id",
            confidence=1.0,
            candidate_categories=[(cat_id, 1.0)],
        )

    # Try phenotype overlap
    if case.hpo_terms:
        scores: dict[str, float] = {}
        query_set = set(case.hpo_terms)

        for cat in index["categories"]:
            cat_terms = {p["hpo_id"] for p in cat.get("phenotypic_features", [])}
            if not cat_terms:
                continue
            jaccard = len(query_set & cat_terms) / len(query_set | cat_terms)
            if jaccard >= min_phenotype_overlap:
                scores[cat["category_id"]] = jaccard

        if scores:
            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            return CategoryMapping(
                case_id=case.case_id,
                category_id=ranked[0][0],
                match_method="phenotype_overlap",
                confidence=ranked[0][1],
                candidate_categories=ranked,
            )

    return CategoryMapping(
        case_id=case.case_id,
        category_id=None,
        match_method="unmatched",
        confidence=0.0,
        candidate_categories=[],
    )


def map_batch(
    cases: list[RareArenaCase],
    categories_dir: Path,
) -> list[CategoryMapping]:
    """Map a batch of cases to patient categories."""
    index = load_category_index(categories_dir)
    mappings = []

    for case in cases:
        mapping = map_case(case, index)
        if mapping.category_id:
            case.patient_category = mapping.category_id
        mappings.append(mapping)

    # Log statistics
    matched = sum(1 for m in mappings if m.category_id)
    logger.info(
        f"Mapped {matched}/{len(cases)} cases "
        f"({matched/len(cases)*100:.1f}% coverage)"
    )

    return mappings
