#!/usr/bin/env python3
"""Build patient category JSON files from orphanet_hypernym.json.

Reads the RareArena-bundled hypernym file (7,476 diseases with parent categories)
and groups diseases under broad top-level categories suitable for model specialization.

Strategy: select parents with >=50 disease_count as category candidates,
then assign each disease to its most specific qualifying parent.
"""

import json
import logging
import re
import sys
from collections import defaultdict
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Minimum disease count for a parent to become a category
MIN_DISEASE_COUNT = 50

# Parents to exclude (too generic or meta-categories)
EXCLUDE_PARENTS = {
    "Rare genetic disease",
    "Rare disease",
    "Genetic disease",
}


def slugify(name: str) -> str:
    """Convert category name to a valid category_id slug."""
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    # Truncate to reasonable length
    if len(s) > 50:
        s = s[:50].rsplit("_", 1)[0]
    return s


def load_hypernym(path: Path) -> list[dict]:
    """Load orphanet_hypernym.json."""
    with open(path) as f:
        return json.load(f)


def select_categories(diseases: list[dict]) -> dict[str, dict]:
    """Select broad categories from parent hierarchy.

    Returns {parent_name: {disease_count, child_count, diseases: []}}.
    """
    parent_stats: dict[str, dict] = {}

    for d in diseases:
        for p in d.get("parents", []):
            name = p["parent"]
            if name in EXCLUDE_PARENTS:
                continue
            dc = p.get("parent_disease_count", 0)
            if name not in parent_stats:
                parent_stats[name] = {
                    "disease_count": dc,
                    "child_count": p.get("parent_child_count", 0),
                    "diseases": [],
                }
            # Track max disease_count seen
            parent_stats[name]["disease_count"] = max(
                parent_stats[name]["disease_count"], dc
            )

    # Filter to broad categories
    categories = {
        name: stats
        for name, stats in parent_stats.items()
        if stats["disease_count"] >= MIN_DISEASE_COUNT
    }

    return categories


def assign_diseases(
    diseases: list[dict],
    categories: dict[str, dict],
) -> dict[str, list[dict]]:
    """Assign each disease to its most specific qualifying category.

    Most specific = smallest disease_count among qualifying parents.
    """
    assignments: dict[str, list[dict]] = defaultdict(list)
    unassigned = 0

    for d in diseases:
        best_cat = None
        best_dc = float("inf")

        for p in d.get("parents", []):
            name = p["parent"]
            if name in categories:
                dc = categories[name]["disease_count"]
                if dc < best_dc:
                    best_dc = dc
                    best_cat = name

        if best_cat:
            assignments[best_cat].append({
                "disease_id": d.get("Orphanetid", ""),
                "name": d.get("name", ""),
                "ordo_id": f"Orphanet_{d['Orphanetid']}" if d.get("Orphanetid") else None,
            })
        else:
            unassigned += 1

    logger.info(
        f"Assigned {sum(len(v) for v in assignments.values())} diseases "
        f"to {len(assignments)} categories ({unassigned} unassigned)"
    )
    return assignments


def build_category_json(
    name: str,
    diseases: list[dict],
    category_stats: dict,
) -> dict:
    """Build a patient_category.schema.json-compliant dict."""
    cat_id = f"rare_cat_{slugify(name)}"

    return {
        "category_id": cat_id,
        "name": name,
        "version": "0.1.0",
        "clustering": {
            "method": "manual_expert",
            "source_graph_version": "orphanet_hypernym_rarearena_2024",
        },
        "diseases": [
            {
                "disease_id": d["disease_id"],
                "name": d["name"],
                "ordo_id": d.get("ordo_id"),
            }
            for d in diseases
        ],
        "phenotypic_features": [],  # Populated by enrich_profiles.py
        "statistics": {
            "disease_count": len(diseases),
            "rarearena_case_count": 0,  # Updated post-ingestion
        },
        "adna": {
            "type": "rare_patient_category",
            "namespace": "rare_",
            "triad": "what",
            "created": "2026-03-18",
            "updated": "2026-03-18",
            "last_edited_by": "agent_stanley",
            "tags": ["rare-disease", "patient-category", "orphanet"],
        },
    }


def main(
    hypernym_path: Path,
    output_dir: Path,
) -> int:
    """Build category files from hypernym data."""
    diseases = load_hypernym(hypernym_path)
    logger.info(f"Loaded {len(diseases)} diseases from {hypernym_path}")

    categories = select_categories(diseases)
    logger.info(f"Selected {len(categories)} broad categories (>={MIN_DISEASE_COUNT} diseases)")

    assignments = assign_diseases(diseases, categories)

    output_dir.mkdir(parents=True, exist_ok=True)
    written = 0

    for name, disease_list in sorted(assignments.items(), key=lambda x: len(x[1]), reverse=True):
        if not disease_list:
            continue

        cat_json = build_category_json(name, disease_list, categories[name])
        filename = f"{cat_json['category_id']}.json"
        out_path = output_dir / filename

        with open(out_path, "w") as f:
            json.dump(cat_json, f, indent=2, ensure_ascii=False)
        written += 1

    logger.info(f"Wrote {written} category files to {output_dir}")
    return written


if __name__ == "__main__":
    hypernym = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "../rarearena-source/benchmark_data/orphanet_hypernym.json"
    )
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(
        "packages/ontology/categories"
    )
    main(hypernym, out)
