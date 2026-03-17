# Rare Archive Compliance — Agentic DNA

## Purpose
aDNA schema validation, FAIR scoring, and governance for the Rare AI Archive.

## Key Components
- `schemas/adna/`: aDNA envelope schemas extending Lattice Protocol ObjectMetadata
- `schemas/fair/`: FAIR scoring criteria adapted for Archive artifacts
- `action/`: Reusable GitHub Action for cross-repo compliance validation
- `src/rare_archive_compliance/`: Python library for validation

## Namespace
Registers the `rare_` namespace in lattice-labs aDNA ontology.
Extends existing Module/Dataset via `module_type`/`dataset_class` discriminators.
