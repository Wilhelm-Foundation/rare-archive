#!/usr/bin/env python3
"""Enrich disease profiles with HPO phenotypes via Orphanet API.

For each unique Orpha_id in the ingested data, fetches phenotype annotations
from the Orphadata REST API and builds DiseaseProfile-compatible records.

Caches results locally to avoid re-fetching on reruns.
Rate-limited to ~3 req/sec to be a good API citizen.
"""

import json
import logging
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Orphadata phenotype endpoint
PHENOTYPE_URL = "https://api.orphadata.com/rd-phenotypes/orphacodes/{code}"
EPIDEMIOLOGY_URL = "https://api.orphadata.com/rd-epidemiology/orphacodes/{code}"
GENES_URL = "https://api.orphadata.com/rd-associated-genes/orphacodes/{code}"

# HPO frequency ID → qualifier mapping
HPO_FREQUENCY_MAP = {
    "HP:0040281": "obligate",
    "HP:0040282": "very_frequent",
    "HP:0040283": "frequent",
    "HP:0040284": "occasional",
    "HP:0040285": "very_rare",
    "HP:0040289": "excluded",
}


def _parse_frequency(freq_str: str) -> str:
    """Parse Orphadata frequency string to our qualifier.

    API returns strings like "Very frequent (99-80%)", "Frequent (79-30%)", etc.
    """
    if not freq_str:
        return "frequent"
    freq_lower = freq_str.lower()
    if "obligate" in freq_lower:
        return "obligate"
    elif "very frequent" in freq_lower:
        return "very_frequent"
    elif "frequent" in freq_lower:
        return "frequent"
    elif "occasional" in freq_lower:
        return "occasional"
    elif "very rare" in freq_lower:
        return "very_rare"
    elif "excluded" in freq_lower:
        return "excluded"
    return "frequent"


def load_disease_index(cases_jsonl: Path) -> dict[str, dict]:
    """Extract unique diseases from ingested cases JSONL.

    Returns {orpha_id: {name, case_count}}.
    """
    index: dict[str, dict] = {}

    with open(cases_jsonl) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            meta = record.get("metadata", {})
            disease_id = meta.get("disease_id") or record.get("disease_id")
            if not disease_id:
                continue

            if disease_id not in index:
                index[disease_id] = {
                    "name": record.get("ground_truth_diagnosis", "")
                    or meta.get("disease_name", ""),
                    "case_count": 0,
                }
            index[disease_id]["case_count"] += 1

    return index


def load_disease_index_from_cases(cases: list[dict]) -> dict[str, dict]:
    """Extract unique diseases from a list of parsed case dicts.

    Returns {orpha_id: {name, case_count}}.
    """
    index: dict[str, dict] = {}
    for case in cases:
        disease_id = case.get("disease_id")
        if not disease_id:
            continue
        if disease_id not in index:
            index[disease_id] = {
                "name": case.get("disease_name", case.get("ground_truth_diagnosis", "")),
                "case_count": 0,
            }
        index[disease_id]["case_count"] += 1
    return index


def fetch_phenotypes(orpha_id: str) -> list[dict] | None:
    """Fetch HPO phenotypes for a disease from Orphadata API."""
    import requests

    url = PHENOTYPE_URL.format(code=orpha_id)
    try:
        resp = requests.get(url, timeout=15.0, headers={
            "User-Agent": "RareArchiveEnrichment/0.1.0",
        })
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning(f"Failed to fetch phenotypes for {orpha_id}: {e}")
        return None

    # Parse the Orphadata response format
    # Structure: data.results.Disorder.HPODisorderAssociation[]
    phenotypes = []
    results = data.get("data", {}).get("results", {})
    if isinstance(results, list):
        results = results[0] if results else {}

    disorder = results.get("Disorder", results)
    associations = disorder.get("HPODisorderAssociation") or []
    if isinstance(associations, dict):
        associations = [associations]

    for assoc in associations:
        hpo_data = assoc.get("HPO", {})
        hpo_id = hpo_data.get("HPOId", "")
        hpo_term = hpo_data.get("HPOTerm", "")

        freq_str = assoc.get("HPOFrequency", "")
        frequency = _parse_frequency(freq_str)

        if hpo_id:
            phenotypes.append({
                "hpo_id": hpo_id,
                "term": hpo_term,
                "frequency": frequency,
            })

    return phenotypes


def enrich_diseases(
    disease_index: dict[str, dict],
    cache_path: Path,
    rate_limit: float = 3.0,
) -> list[dict]:
    """Enrich all diseases with phenotype data.

    Uses local file cache to avoid re-fetching.
    """
    # Load existing cache
    cache: dict[str, dict] = {}
    if cache_path.exists():
        with open(cache_path) as f:
            cache = json.load(f)
        logger.info(f"Loaded {len(cache)} cached profiles")

    profiles = []
    to_fetch = [oid for oid in disease_index if oid not in cache]
    logger.info(f"{len(disease_index)} unique diseases, {len(to_fetch)} need API fetch")

    interval = 1.0 / rate_limit
    fetched = 0
    failed = 0

    for i, orpha_id in enumerate(to_fetch):
        if i > 0:
            time.sleep(interval)

        phenotypes = fetch_phenotypes(orpha_id)

        if phenotypes is not None:
            cache[orpha_id] = {
                "disease_id": orpha_id,
                "disease_name": disease_index[orpha_id]["name"],
                "hpo_phenotypes": phenotypes,
            }
            fetched += 1
        else:
            cache[orpha_id] = {
                "disease_id": orpha_id,
                "disease_name": disease_index[orpha_id]["name"],
                "hpo_phenotypes": [],
            }
            failed += 1

        if (i + 1) % 100 == 0:
            logger.info(f"  Fetched {i + 1}/{len(to_fetch)} ({fetched} ok, {failed} failed)")
            # Periodic cache save
            with open(cache_path, "w") as f:
                json.dump(cache, f, ensure_ascii=False)

    # Final cache save
    with open(cache_path, "w") as f:
        json.dump(cache, f, ensure_ascii=False)
    logger.info(f"Enrichment complete: {fetched} fetched, {failed} failed, {len(cache)} total cached")

    # Build profile list for all diseases in the index
    for orpha_id, info in disease_index.items():
        cached = cache.get(orpha_id, {})
        profiles.append({
            "disease_id": orpha_id,
            "disease_name": info["name"],
            "ordo_id": f"Orphanet_{orpha_id}",
            "hpo_phenotypes": cached.get("hpo_phenotypes", []),
            "inheritance_patterns": [],
            "age_of_onset": [],
            "prevalence": None,
            "case_count": info["case_count"],
        })

    return profiles


def export_profiles(profiles: list[dict], output_path: Path) -> int:
    """Export disease profiles as JSONL."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with open(output_path, "w") as f:
        for p in profiles:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
            count += 1
    logger.info(f"Exported {count} profiles to {output_path}")
    return count


if __name__ == "__main__":
    cases_jsonl = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/rarearena_rds_train.jsonl")
    cache = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/disease_profiles_cache.json")
    output = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("data/disease_profiles.jsonl")

    index = load_disease_index(cases_jsonl)
    profiles = enrich_diseases(index, cache)
    export_profiles(profiles, output)
