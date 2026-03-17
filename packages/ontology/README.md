# Rare Archive Ontology

Four ontology domains for the [Rare AI Archive](https://github.com/wilhelm-foundation/rare-ai-archive):

1. **Patient Category** — Clusters of rare diseases grouped by shared phenotypic and genetic features
2. **Clinical Tool** — Catalog of diagnostic tools with API specs and dependency graphs
3. **Model** — HuggingFace model variant tracking across training stages
4. **Dataset** — HuggingFace dataset tracking with provenance chains

## Installation

```bash
pip install -e .

# With clustering support (node2vec, scikit-learn):
pip install -e ".[clustering]"
```

## Schemas

All schemas use JSON Schema draft 2020-12 with JSON-LD context:

- `schemas/patient_category.schema.json` — Disease clusters
- `schemas/clinical_tool.schema.json` — Diagnostic tool definitions
- `schemas/model.schema.json` — Model variant metadata
- `schemas/dataset.schema.json` — Dataset metadata

## Alignment Files

- `alignment/hpo_ordo_alignment.yaml` — HPO ↔ ORDO mapping via HOOM
- `alignment/mondo_crosswalk.yaml` — Cross-reference via Mondo Disease Ontology
- `alignment/rdcdm_mapping.yaml` — RD-CDM interoperability mapping

## Namespace

Uses the `rare_` namespace extension in the Lattice Protocol aDNA ontology. All four domains are WHAT entities.

## License

Apache 2.0
