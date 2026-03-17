# Rare Archive Datasets

Dataset curation pipelines for the [Rare AI Archive](https://github.com/wilhelm-foundation/rare-ai-archive).

## Pipelines

### RareArena Ingestion
Ingests the [RareArena](https://huggingface.co/datasets/RareArena) benchmark (~50K cases, 4K+ diseases):

```python
from rare_archive_datasets.ingestion.rarearena import ingest_split, export_for_training

cases = ingest_split(Path("data/rarearena_rds.jsonl"), split="rds")
export_for_training(cases, Path("output/train.jsonl"), format="chat")
```

### Synthetic Patient Generator
Generates synthetic clinical vignettes from disease profiles (no real PHI):

```python
from rare_archive_datasets.synthetic.patient_generator import load_disease_profiles, generate_batch

profiles = load_disease_profiles(Path("data/disease_profiles.json"))
patients = generate_batch(profiles, n_per_profile=3, seed=42)
```

### Patient Category Assignment
Maps cases to ontology patient categories:

```python
from rare_archive_datasets.assignment.category_mapper import map_batch

mappings = map_batch(cases, categories_dir=Path("../rare-archive-ontology/schemas/categories/"))
```

## Published Datasets (HuggingFace)

| Dataset | Description |
|---------|-------------|
| `rare-archive-eval-rarearena-rds` | RareArena Rare Disease Specialists split |
| `rare-archive-eval-rarearena-rdc` | RareArena Rare Disease Cases split |
| `rare-archive-synthetic-patients` | Synthetic patient vignettes |

## License

Apache 2.0 (code). Datasets inherit their source licenses (e.g., CC BY-NC-SA 4.0 for RareArena derivatives).
