# Rare AI Archive — Agentic DNA

## Purpose
Meta-repository and front door for the Rare AI Archive: a decentralized post-training, model validation, and clinical deployment ecosystem for rare genetic diseases.

## Triad Structure
- **what/**: Domain knowledge — ontology context, architecture specs, ADRs
- **how/**: Operations — campaign plans, session tracking, templates
- **who/**: Organization — governance policies, team coordination

## Monorepo Packages
| Package | Path | Purpose |
|---------|------|---------|
| ontology | `packages/ontology/` | 4 ontology domains, JSON-LD schemas, clustering |
| models | `packages/models/` | 4-stage training pipeline, eval harnesses, GGUF quantization |
| datasets | `packages/datasets/` | RareArena ingestion, synthetic patients, preference data |
| rlhf | `packages/rlhf/` | RLHF portal backend, ELO arena, expert matching |
| tools | `packages/tools/` | Clinical tool harness (ClinVar, Orphanet, PanelApp, gnomAD, HPO, PubMed) |
| compliance | `packages/compliance/` | aDNA schemas, FAIR scoring, governance, CI validation |
| deploy | `deploy/` | L1/L2 Docker Compose overlays, nginx, GGUF download |
| docs | `docs/` | Guides: quantization, evaluation, troubleshooting, tool integration, L1 setup |
