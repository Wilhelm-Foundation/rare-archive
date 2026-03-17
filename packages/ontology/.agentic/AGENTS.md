# Rare Archive Ontology — Agentic DNA

## Purpose
Four ontology domains for the Rare AI Archive: Patient Category, Clinical Tool, Model, Dataset.
All domains are WHAT entities in the aDNA ontology, using the `rare_` namespace extension.

## Key Directories
- `schemas/`: JSON-LD schemas for all 4 domains
- `alignment/`: HPO↔ORDO (via HOOM), Mondo crosswalk, RD-CDM mapping files
- `clustering/`: Sanjak et al. disease clustering (node2vec + K-means on HPO/ORDO/Mondo graph)
- `src/rare_archive_ontology/`: Python package for schema validation and category assignment

## Ontology Domains
1. **Patient Category** — Disease clusters by shared phenotypic/genetic features
2. **Clinical Tool** — Diagnostic tool catalog with API specs and dependency graphs
3. **Model** — HuggingFace model variant tracking (arch, params, quant, LoRA stage, ELO)
4. **Dataset** — HuggingFace dataset tracking (provenance chains, consent governance)
