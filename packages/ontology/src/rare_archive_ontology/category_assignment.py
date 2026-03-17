"""Patient category assignment — maps diseases/cases to ontology categories.

Loads patient category definitions and assigns cases to the most appropriate
category based on disease ID matching, HPO phenotype overlap, or embedding
similarity (when node2vec embeddings are available).
"""

import json
from pathlib import Path
from typing import Any


def load_categories(categories_dir: Path) -> list[dict]:
    """Load all patient category definitions from a directory of JSON files."""
    categories = []
    for f in sorted(categories_dir.glob("*.json")):
        with open(f) as fh:
            categories.append(json.load(fh))
    return categories


def assign_by_disease_id(
    disease_id: str,
    categories: list[dict],
) -> str | None:
    """Assign a disease to a patient category by exact disease ID match.

    Checks ORDO, OMIM, Mondo, and GARD identifiers.
    Returns category_id or None if no match.
    """
    for cat in categories:
        for disease in cat.get("diseases", []):
            ids = [
                disease.get("disease_id"),
                disease.get("ordo_id"),
                disease.get("omim_id"),
                disease.get("mondo_id"),
                disease.get("gard_id"),
            ]
            if disease_id in [i for i in ids if i is not None]:
                return cat["category_id"]
    return None


def assign_by_phenotype_overlap(
    hpo_terms: list[str],
    categories: list[dict],
    min_overlap: float = 0.3,
) -> list[tuple[str, float]]:
    """Assign a case to patient categories by HPO phenotype overlap.

    Returns list of (category_id, overlap_score) sorted by descending score.
    Only returns categories with overlap >= min_overlap.
    """
    results = []
    query_set = set(hpo_terms)

    for cat in categories:
        cat_terms = {f["hpo_id"] for f in cat.get("phenotypic_features", [])}
        if not cat_terms:
            continue

        overlap = len(query_set & cat_terms) / len(query_set | cat_terms)
        if overlap >= min_overlap:
            results.append((cat["category_id"], overlap))

    return sorted(results, key=lambda x: x[1], reverse=True)


def compute_coverage(
    disease_ids: list[str],
    categories: list[dict],
) -> dict[str, Any]:
    """Compute coverage statistics: how many diseases are assigned to categories.

    Returns dict with total_diseases, assigned_count, unassigned_count,
    coverage_pct, and unassigned_ids.
    """
    assigned = set()
    all_cat_disease_ids = set()

    for cat in categories:
        for disease in cat.get("diseases", []):
            for key in ["disease_id", "ordo_id", "omim_id", "mondo_id", "gard_id"]:
                val = disease.get(key)
                if val:
                    all_cat_disease_ids.add(val)

    for did in disease_ids:
        if did in all_cat_disease_ids:
            assigned.add(did)

    unassigned = [d for d in disease_ids if d not in assigned]

    return {
        "total_diseases": len(disease_ids),
        "assigned_count": len(assigned),
        "unassigned_count": len(unassigned),
        "coverage_pct": (len(assigned) / len(disease_ids) * 100) if disease_ids else 0,
        "unassigned_ids": unassigned,
    }
