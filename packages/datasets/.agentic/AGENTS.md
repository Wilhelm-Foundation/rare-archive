# Rare Archive Datasets — Agentic DNA

## Purpose
Dataset curation pipelines: RareArena ingestion, synthetic patient generation, patient-category assignment.

## Key Directories
- `src/rare_archive_datasets/ingestion/`: RareArena JSONL ingestion (RDS + RDC splits)
- `src/rare_archive_datasets/synthetic/`: Synthetic patient generator (Orphanet/HPO → clinical vignettes)
- `src/rare_archive_datasets/assignment/`: Patient-category assignment (cases → ontology categories)
- `templates/`: aDNA-aligned dataset card templates

## Published Datasets (HuggingFace)
- `rare-archive-eval-rarearena-rds`: RareArena Rare Disease Specialists split
- `rare-archive-eval-rarearena-rdc`: RareArena Rare Disease Cases split
