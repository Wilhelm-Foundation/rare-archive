#!/usr/bin/env python3
"""Publish datasets to HuggingFace under wilhelm-foundation org.

Uploads JSONL files with auto-generated dataset cards.
License: CC BY-NC-SA 4.0 (matching RareArena source).
"""

import json
import logging
import sys
from pathlib import Path
from string import Template

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def make_dataset_card(
    name: str,
    description: str,
    dataset_type: str,
    license_str: str,
    version: str,
    field_descriptions: str,
    split_table: str,
    source_description: str,
    processing_description: str,
    phi_status: str,
    phi_description: str,
    category_list: str,
    intended_use: str,
    limitations: str,
    size_category: str = "10K<n<100K",
) -> str:
    """Generate a HuggingFace dataset card from the template."""
    template = """---
dataset_info:
  name: ${name}
  version: ${version}
  license: ${license}
  description: ${description}
tags:
  - rare-disease
  - clinical-diagnostics
  - ${dataset_type}
  - rare-ai-archive
task_categories:
  - text-generation
  - question-answering
language:
  - en
size_categories:
  - ${size_category}
---

# ${name}

${description}

## Dataset Description

- **Repository:** [wilhelm-foundation/${name}](https://huggingface.co/datasets/wilhelm-foundation/${name})
- **License:** ${license}
- **Version:** ${version}
- **Part of:** [Rare AI Archive](https://github.com/wilhelm-foundation/rare-ai-archive)

## Dataset Structure

### Data Fields

${field_descriptions}

### Data Splits

| Split | Records |
|-------|---------|
${split_table}

## Dataset Creation

### Source Data

${source_description}

### Data Processing

${processing_description}

### PHI Status

**${phi_status}** — ${phi_description}

## Patient Categories

This dataset covers the following patient categories:

${category_list}

## Intended Use

${intended_use}

## Limitations

${limitations}

## Citation

If you use this dataset, please cite:

```bibtex
@misc{rarearena2024,
  title={RareArena: A Benchmark for Rare Disease Diagnosis},
  author={Zhao, Zhiyu and others},
  year={2024},
  url={https://github.com/zhao-zy15/RareArena}
}
```
"""
    return Template(template).safe_substitute(
        name=name,
        description=description,
        dataset_type=dataset_type,
        license=license_str,
        version=version,
        field_descriptions=field_descriptions,
        split_table=split_table,
        source_description=source_description,
        processing_description=processing_description,
        phi_status=phi_status,
        phi_description=phi_description,
        category_list=category_list,
        intended_use=intended_use,
        limitations=limitations,
        size_category=size_category,
    )


def count_jsonl(path: Path) -> int:
    """Count records in a JSONL file."""
    count = 0
    with open(path) as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def publish_dataset(
    repo_id: str,
    files: dict[str, Path],
    readme_content: str,
    private: bool = False,
) -> str:
    """Create HF repo and upload files.

    Args:
        repo_id: e.g. "wilhelm-foundation/rare-archive-eval-rarearena-rds"
        files: {filename_in_repo: local_path}
        readme_content: Dataset card markdown
        private: Whether repo should be private

    Returns:
        Repo URL
    """
    from huggingface_hub import HfApi

    api = HfApi()

    # Create repo (idempotent)
    api.create_repo(
        repo_id=repo_id,
        repo_type="dataset",
        private=private,
        exist_ok=True,
    )

    # Upload README
    api.upload_file(
        path_or_fileobj=readme_content.encode("utf-8"),
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type="dataset",
    )

    # Upload data files
    for repo_path, local_path in files.items():
        logger.info(f"  Uploading {local_path} -> {repo_path}")
        api.upload_file(
            path_or_fileobj=str(local_path),
            path_in_repo=repo_path,
            repo_id=repo_id,
            repo_type="dataset",
        )

    url = f"https://huggingface.co/datasets/{repo_id}"
    logger.info(f"Published {repo_id}: {url}")
    return url


def publish_eval_rds(data_dir: Path) -> str:
    """Publish RDS evaluation dataset."""
    eval_file = data_dir / "rarearena_eval_rds.jsonl"
    n = count_jsonl(eval_file)

    card = make_dataset_card(
        name="rare-archive-eval-rarearena-rds",
        description="RareArena RDS (Rare Disease Specialists) evaluation benchmark. 8,562 clinical vignettes across 4,000+ rare diseases for evaluating diagnostic reasoning.",
        dataset_type="rarearena_eval",
        license_str="CC BY-NC-SA 4.0",
        version="0.1.0",
        field_descriptions="| Field | Type | Description |\n|-------|------|-------------|\n| `messages` | list | Chat-format messages (system, user vignette, assistant diagnosis) |\n| `metadata.case_id` | string | Unique case identifier |\n| `metadata.split` | string | Source split (rds) |\n| `metadata.disease_id` | string | Orphanet disease ID |",
        split_table=f"| eval | {n:,} |",
        source_description="Derived from [RareArena](https://github.com/zhao-zy15/RareArena) RDS benchmark split. Cases are PMC case reports rewritten by GPT-4o for de-identification.",
        processing_description="Ingested via rare-archive-datasets v0.1.0 parse_case() (v3 format). Exported as OpenAI chat format JSONL.",
        phi_status="no_phi",
        phi_description="All vignettes are GPT-4o rewrites of published case reports. No real patient data.",
        category_list="All RareArena disease categories (~4,500 unique diseases).",
        intended_use="Evaluation of rare disease diagnostic models. Top-5 differential diagnosis accuracy.",
        limitations="English only. Biased toward diseases with published case reports. GPT-4o rewriting may alter clinical nuance.",
        size_category="1K<n<10K",
    )

    return publish_dataset(
        repo_id="wilhelm-foundation/rare-archive-eval-rarearena-rds",
        files={"data/eval.jsonl": eval_file},
        readme_content=card,
    )


def publish_eval_rdc(data_dir: Path) -> str:
    """Publish RDC evaluation dataset."""
    eval_file = data_dir / "rarearena_eval_rdc.jsonl"
    n = count_jsonl(eval_file)

    card = make_dataset_card(
        name="rare-archive-eval-rarearena-rdc",
        description="RareArena RDC (Rare Disease Cases) evaluation benchmark. 4,376 clinical vignettes with test results across rare diseases for evaluating diagnostic reasoning with lab data.",
        dataset_type="rarearena_eval",
        license_str="CC BY-NC-SA 4.0",
        version="0.1.0",
        field_descriptions="| Field | Type | Description |\n|-------|------|-------------|\n| `messages` | list | Chat-format messages (system, user vignette + test results, assistant diagnosis) |\n| `metadata.case_id` | string | Unique case identifier |\n| `metadata.split` | string | Source split (rdc) |\n| `metadata.disease_id` | string | Orphanet disease ID |",
        split_table=f"| eval | {n:,} |",
        source_description="Derived from [RareArena](https://github.com/zhao-zy15/RareArena) RDC benchmark split. Cases include both clinical vignettes and test results.",
        processing_description="Ingested via rare-archive-datasets v0.1.0 parse_case() (v3 format). Test results concatenated to vignette. Exported as OpenAI chat format JSONL.",
        phi_status="no_phi",
        phi_description="All vignettes are GPT-4o rewrites of published case reports. No real patient data.",
        category_list="All RareArena disease categories.",
        intended_use="Evaluation of rare disease diagnostic models with lab/test result interpretation.",
        limitations="English only. Biased toward diseases with published case reports.",
        size_category="1K<n<10K",
    )

    return publish_dataset(
        repo_id="wilhelm-foundation/rare-archive-eval-rarearena-rdc",
        files={"data/eval.jsonl": eval_file},
        readme_content=card,
    )


def publish_synthetic(data_dir: Path) -> str:
    """Publish synthetic patients dataset."""
    synth_file = data_dir / "synthetic_patients.jsonl"
    profiles_file = data_dir / "disease_profiles.jsonl"
    n = count_jsonl(synth_file)

    card = make_dataset_card(
        name="rare-archive-synthetic-patients",
        description=f"Synthetic rare disease patient vignettes generated from Orphanet disease profiles. {n:,} cases across ~4,500 diseases at easy/medium/hard difficulty levels.",
        dataset_type="synthetic_patients",
        license_str="CC BY-NC-SA 4.0",
        version="0.1.0",
        field_descriptions="| Field | Type | Description |\n|-------|------|-------------|\n| `patient_id` | string | Unique synthetic patient ID |\n| `clinical_vignette` | string | Generated clinical presentation |\n| `ground_truth_diagnosis` | string | Disease name |\n| `disease_id` | string | Orphanet disease ID |\n| `hpo_terms_present` | list | HPO terms sampled as present |\n| `hpo_terms_absent` | list | HPO terms sampled as absent |\n| `age` | int | Patient age |\n| `sex` | string | Patient sex |\n| `difficulty` | string | easy/medium/hard |\n| `family_history` | string | Generated family history |",
        split_table=f"| train | {n:,} |",
        source_description="Generated from Orphanet disease profiles enriched with HPO phenotype annotations via Orphadata API.",
        processing_description="Disease profiles fetched from Orphadata rd-phenotypes endpoint. Synthetic patients generated via frequency-weighted HPO term sampling with difficulty modifiers.",
        phi_status="synthetic_only",
        phi_description="All patients are computationally generated. No real patient data involved.",
        category_list="All Orphanet rare diseases with available phenotype profiles.",
        intended_use="Stage 1 SFT training data for rare disease diagnostic models. Augments real RareArena cases.",
        limitations="Formulaic vignette structure. Symptom sampling may not capture complex phenotypic correlations. Quality assessment in M07.",
        size_category="10K<n<100K",
    )

    files = {"data/synthetic_patients.jsonl": synth_file}
    if profiles_file.exists():
        files["data/disease_profiles.jsonl"] = profiles_file

    return publish_dataset(
        repo_id="wilhelm-foundation/rare-archive-synthetic-patients",
        files=files,
        readme_content=card,
    )


if __name__ == "__main__":
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data")

    from huggingface_hub import login
    login()  # Will prompt for token or use HF_TOKEN env var

    urls = []
    urls.append(publish_eval_rds(data_dir))
    urls.append(publish_eval_rdc(data_dir))
    urls.append(publish_synthetic(data_dir))

    print("\nPublished datasets:")
    for url in urls:
        print(f"  {url}")
