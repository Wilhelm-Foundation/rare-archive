# Rare AI Archive — CLAUDE.md

## Project Overview
The Rare AI Archive is a decentralized post-training, model validation, and clinical deployment ecosystem for rare genetic diseases — a program of the Wilhelm Foundation.

## Repository Structure
This is a monorepo. All components live under `packages/` (Python packages) or `deploy/` (infrastructure).

```
rare-archive/
├── packages/
│   ├── ontology/       # Disease schemas, alignment maps, clustering
│   ├── compliance/     # aDNA validation, FAIR scoring
│   ├── datasets/       # RareArena ingestion, synthetic patients
│   ├── models/         # 4-stage training pipeline, GGUF quantization
│   ├── tools/          # Clinical tool harness (ClinVar, Orphanet, etc.)
│   └── rlhf/           # RLHF portal backend, ELO arena
├── deploy/             # L1/L2 Docker Compose, nginx, GGUF download
├── scripts/            # setup_dev.sh, validate_archive.py
└── .agentic/           # Root-level aDNA triad
```

## Key Commands
```bash
# Install all packages in dev mode
./scripts/setup_dev.sh

# Validate all packages
python scripts/validate_archive.py .
```

## Naming Conventions
- **Files**: underscores (e.g., `patient_category.schema.json`)
- **HuggingFace names**: hyphens (e.g., `rare-archive-qwen3.5-4b-sft-lora-v1`)
- **aDNA types**: `rare_` namespace prefix (e.g., `rare_patient_category`)
- **Tiers**: Always UPPERCASE (L1, L2, L3)

## Architecture Decisions
- Unsloth for all model sizes (dense and MoE)
- llama.cpp over vLLM for L2 inference (GGUF control, mmap loading)
- Separate Docker Compose overlay (don't modify L2 stack)
- GPU 3 dedicated to Archive inference
- Synthetic patients only, never real PHI
- `rare_` namespace extension in aDNA, not new entity types
