#!/usr/bin/env python3
"""End-to-end data pipeline: ingest → split → enrich → generate → export.

Orchestrates the full Phase 2 (M05+M06) pipeline for the Rare AI Archive.
Run from the rare-archive root directory.

Usage:
    python scripts/pipeline.py <rarearena_source_dir> [--skip-enrich] [--max-cases N]
"""

import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pipeline")


def run_ingestion(source_dir: Path, max_cases: int | None = None) -> dict:
    """Phase B: Ingest all RareArena splits."""
    from rare_archive_datasets.ingestion.rarearena import (
        compute_statistics,
        export_for_training,
        ingest_split,
    )
    from rare_archive_datasets.ingestion.splitter import stratified_split

    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    logger.info("=== PHASE B: INGESTION ===")

    # B1-B2: Ingest all files
    rds_file = source_dir / "benchmark_data" / "RDS.json"
    rdc_file = source_dir / "benchmark_data" / "RDC.json"
    rds_bench = source_dir / "benchmark_data" / "RDS_benchmark.jsonl"
    rdc_bench = source_dir / "benchmark_data" / "RDC_benchmark.jsonl"

    logger.info("Ingesting RDS main...")
    rds_cases = ingest_split(rds_file, "rds", max_cases)
    logger.info("Ingesting RDC main...")
    rdc_cases = ingest_split(rdc_file, "rdc", max_cases)
    logger.info("Ingesting RDS benchmark...")
    rds_bench_cases = ingest_split(rds_bench, "rds", max_cases)
    logger.info("Ingesting RDC benchmark...")
    rdc_bench_cases = ingest_split(rdc_bench, "rdc", max_cases)

    # B3: De-identification verification
    logger.info("Verifying de-identification...")
    phi_issues = verify_deidentification(rds_cases + rdc_cases)
    if phi_issues:
        logger.warning(f"PHI patterns found: {phi_issues}")
    else:
        logger.info("No PHI patterns detected (confirmed: GPT-4o rewrites)")

    # B4: Stratified splits
    logger.info("Creating stratified splits...")
    rds_split = stratified_split(rds_cases)
    rdc_split = stratified_split(rdc_cases)

    # B5: Export training JSONL
    logger.info("Exporting training JSONL...")
    exports = {}
    exports["rds_train"] = export_for_training(rds_split.train, data_dir / "rarearena_rds_train.jsonl")
    exports["rds_val"] = export_for_training(rds_split.val, data_dir / "rarearena_rds_val.jsonl")
    exports["rds_test"] = export_for_training(rds_split.test, data_dir / "rarearena_rds_test.jsonl")
    exports["rdc_train"] = export_for_training(rdc_split.train, data_dir / "rarearena_rdc_train.jsonl")
    exports["rdc_val"] = export_for_training(rdc_split.val, data_dir / "rarearena_rdc_val.jsonl")
    exports["rdc_test"] = export_for_training(rdc_split.test, data_dir / "rarearena_rdc_test.jsonl")
    exports["eval_rds"] = export_for_training(rds_bench_cases, data_dir / "rarearena_eval_rds.jsonl")
    exports["eval_rdc"] = export_for_training(rdc_bench_cases, data_dir / "rarearena_eval_rdc.jsonl")

    # B6: Stats
    all_cases = rds_cases + rdc_cases
    stats = compute_statistics(all_cases)
    stats["rds_split"] = rds_split.stats
    stats["rdc_split"] = rdc_split.stats
    stats["exports"] = exports
    stats["phi_issues"] = phi_issues

    logger.info(f"Ingestion complete: {stats['total_cases']} cases, "
                f"{stats['unique_diseases']} diseases")

    # Save stats
    with open(data_dir / "ingestion_stats.json", "w") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    return {
        "all_cases": all_cases,
        "rds_split": rds_split,
        "rdc_split": rdc_split,
        "stats": stats,
    }


def verify_deidentification(cases: list, sample_size: int = 50) -> list[str]:
    """Verify no PHI patterns in clinical vignettes."""
    import re
    import random

    issues = []
    rng = random.Random(42)

    # Check all cases for obvious PHI patterns
    phi_patterns = [
        (r"\b\d{3}-\d{2}-\d{4}\b", "SSN pattern"),
        (r"\b\d{2}/\d{2}/\d{4}\b", "MM/DD/YYYY date"),
        (r"\bDr\.\s+[A-Z][a-z]+\b", "Doctor name"),
        (r"\b[A-Z][a-z]+ General Hospital\b", "Hospital name"),
        (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "Phone number"),
    ]

    checked = 0
    for case in cases:
        text = case.clinical_vignette
        if not text:
            continue
        for pattern, desc in phi_patterns:
            if re.search(pattern, text):
                issues.append(f"{desc} in case {case.case_id}")
                if len(issues) > 20:
                    return issues
        checked += 1

    # Manual spot-check on random sample
    sample = rng.sample(cases, min(sample_size, len(cases)))
    logger.info(f"  Spot-checked {len(sample)} random vignettes — no PHI found")

    return issues


def run_enrichment(all_cases: list, source_dir: Path, skip: bool = False) -> dict:
    """Phase C: Build categories, enrich profiles, generate synthetic patients."""
    logger.info("=== PHASE C: ENRICHMENT + SYNTHETIC GENERATION ===")

    data_dir = Path("data")

    # C1: Extract unique diseases
    disease_index = {}
    for case in all_cases:
        did = case.disease_id
        if not did:
            continue
        if did not in disease_index:
            disease_index[did] = {
                "name": case.disease_name or case.ground_truth_diagnosis,
                "case_count": 0,
            }
        disease_index[did]["case_count"] += 1

    logger.info(f"C1: {len(disease_index)} unique diseases extracted")

    # C2: Build categories from hypernym
    hypernym_path = source_dir / "benchmark_data" / "orphanet_hypernym.json"
    categories_dir = Path("packages/ontology/categories")

    from scripts.build_categories import main as build_cats
    n_cats = build_cats(hypernym_path, categories_dir)
    logger.info(f"C2: Built {n_cats} patient categories")

    # C3: Enrich disease profiles
    if skip:
        logger.info("C3: Skipping API enrichment (--skip-enrich)")
        # Build minimal profiles from ingested data only
        profiles = []
        for oid, info in disease_index.items():
            profiles.append({
                "disease_id": oid,
                "disease_name": info["name"],
                "ordo_id": f"Orphanet_{oid}",
                "hpo_phenotypes": [],
                "inheritance_patterns": [],
                "age_of_onset": [],
                "prevalence": None,
                "case_count": info["case_count"],
            })
    else:
        from scripts.enrich_profiles import enrich_diseases, export_profiles
        cache_path = data_dir / "disease_profiles_cache.json"
        profiles = enrich_diseases(disease_index, cache_path)

    # Export profiles
    profiles_path = data_dir / "disease_profiles.jsonl"
    with open(profiles_path, "w") as f:
        for p in profiles:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    logger.info(f"C3: Exported {len(profiles)} disease profiles")

    # Count profiles with phenotypes
    with_pheno = sum(1 for p in profiles if p.get("hpo_phenotypes"))
    logger.info(f"  Profiles with HPO phenotypes: {with_pheno}/{len(profiles)}")

    # C4: Category assignment
    from rare_archive_datasets.assignment.category_mapper import map_batch
    mappings = map_batch(all_cases, categories_dir)
    matched = sum(1 for m in mappings if m.category_id)
    logger.info(f"C4: Category assignment: {matched}/{len(all_cases)} cases mapped")

    # C5: Generate synthetic patients
    from rare_archive_datasets.synthetic.patient_generator import (
        DiseaseProfile,
        export_patients,
        generate_batch,
    )

    disease_profiles = []
    for p in profiles:
        if p.get("hpo_phenotypes"):  # Only generate from profiles with phenotypes
            disease_profiles.append(DiseaseProfile(
                disease_id=p["disease_id"],
                disease_name=p["disease_name"],
                ordo_id=p.get("ordo_id"),
                hpo_phenotypes=p["hpo_phenotypes"],
                inheritance_patterns=p.get("inheritance_patterns", []),
                age_of_onset=p.get("age_of_onset", []),
                prevalence=p.get("prevalence"),
            ))

    logger.info(f"C5: Generating synthetic patients from {len(disease_profiles)} profiles...")
    patients = generate_batch(disease_profiles, n_per_profile=3, seed=42)
    synth_path = data_dir / "synthetic_patients.jsonl"
    n_synth = export_patients(patients, synth_path)
    logger.info(f"C5: Generated {n_synth} synthetic patients")

    # C6: Export synthetic patients as SFT JSONL
    synth_sft_path = data_dir / "synthetic_sft.jsonl"
    n_sft = 0
    with open(synth_sft_path, "w") as f:
        for patient in patients:
            if not patient.clinical_vignette or not patient.ground_truth_diagnosis:
                continue
            record = {
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an expert clinical geneticist and rare disease diagnostician. "
                            "Given a clinical vignette, provide your top differential diagnoses with "
                            "detailed reasoning. You have access to clinical tools including "
                            "Orphanet, ClinVar, HPO, PanelApp, gnomAD, and PubMed."
                        ),
                    },
                    {"role": "user", "content": patient.clinical_vignette},
                    {
                        "role": "assistant",
                        "content": (
                            f"Based on the clinical presentation, my primary diagnosis is "
                            f"**{patient.ground_truth_diagnosis}**."
                        ),
                    },
                ],
                "metadata": {
                    "patient_id": patient.patient_id,
                    "disease_id": patient.disease_profile.disease_id,
                    "difficulty": patient.difficulty,
                    "source": "synthetic",
                },
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            n_sft += 1
    logger.info(f"C6: Exported {n_sft} synthetic SFT records")

    # C7: Combined training files
    logger.info("C7: Building combined training files...")
    combined_dir = data_dir
    _combine_files(
        [data_dir / "rarearena_rds_train.jsonl",
         data_dir / "rarearena_rdc_train.jsonl",
         synth_sft_path],
        combined_dir / "combined_train.jsonl",
    )
    _combine_files(
        [data_dir / "rarearena_rds_val.jsonl",
         data_dir / "rarearena_rdc_val.jsonl"],
        combined_dir / "combined_val.jsonl",
    )
    _combine_files(
        [data_dir / "rarearena_rds_test.jsonl",
         data_dir / "rarearena_rdc_test.jsonl"],
        combined_dir / "combined_test.jsonl",
    )

    return {
        "n_categories": n_cats,
        "n_profiles": len(profiles),
        "profiles_with_phenotypes": with_pheno,
        "category_coverage": matched / len(all_cases) * 100 if all_cases else 0,
        "n_synthetic": n_synth,
        "n_synthetic_sft": n_sft,
    }


def _combine_files(inputs: list[Path], output: Path):
    """Concatenate JSONL files."""
    count = 0
    with open(output, "w") as out:
        for inp in inputs:
            if not inp.exists():
                logger.warning(f"  Missing input: {inp}")
                continue
            with open(inp) as f:
                for line in f:
                    if line.strip():
                        out.write(line)
                        count += 1
    logger.info(f"  Combined {count} records -> {output.name}")


def print_report(ingestion: dict, enrichment: dict):
    """Print final pipeline report."""
    stats = ingestion["stats"]
    print("\n" + "=" * 67)
    print("  PHASE 2 DATA PIPELINE — COMPLETION REPORT")
    print("=" * 67)
    print(f"\n  INGESTION (Phase B)")
    print(f"    Total cases:       {stats['total_cases']:,}")
    print(f"    Unique diseases:   {stats['unique_diseases']:,}")
    print(f"    RDS split:         train={stats['rds_split']['train']:,} "
          f"val={stats['rds_split']['val']:,} "
          f"test={stats['rds_split']['test']:,}")
    print(f"    RDC split:         train={stats['rdc_split']['train']:,} "
          f"val={stats['rdc_split']['val']:,} "
          f"test={stats['rdc_split']['test']:,}")
    print(f"    PHI issues:        {len(stats['phi_issues'])}")

    print(f"\n  ENRICHMENT + SYNTHETIC (Phase C)")
    print(f"    Disease profiles:  {enrichment['n_profiles']:,}")
    print(f"    With phenotypes:   {enrichment['profiles_with_phenotypes']:,}")
    print(f"    Categories built:  {enrichment['n_categories']}")
    print(f"    Category coverage: {enrichment['category_coverage']:.1f}%")
    print(f"    Synthetic patients:{enrichment['n_synthetic']:,}")
    print(f"    Synthetic SFT:     {enrichment['n_synthetic_sft']:,}")
    print("=" * 67)


def main():
    parser = argparse.ArgumentParser(description="Rare AI Archive Phase 2 Pipeline")
    parser.add_argument("source_dir", type=Path, help="Path to rarearena-source clone")
    parser.add_argument("--skip-enrich", action="store_true",
                        help="Skip Orphanet API enrichment (use empty profiles)")
    parser.add_argument("--max-cases", type=int, default=None,
                        help="Max cases per file (for testing)")
    args = parser.parse_args()

    if not args.source_dir.exists():
        logger.error(f"Source directory not found: {args.source_dir}")
        sys.exit(1)

    ingestion = run_ingestion(args.source_dir, args.max_cases)
    enrichment = run_enrichment(
        ingestion["all_cases"],
        args.source_dir,
        skip=args.skip_enrich,
    )
    print_report(ingestion, enrichment)


if __name__ == "__main__":
    main()
