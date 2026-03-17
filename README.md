# Rare AI Archive

**A decentralized post-training, model validation, and clinical deployment ecosystem for rare genetic diseases.**

*A program of the [Wilhelm Foundation](https://wilhelm.foundation)*

---

300 million people worldwide live with a rare disease. The average diagnostic odyssey takes 5–7 years. During that time, families navigate a maze of specialists, tests, and uncertainty — often without ever receiving a diagnosis.

The Rare AI Archive exists to close that gap.

We build open-source AI models specialized in rare disease diagnostics, validated by the clinicians who treat these patients, and deployable at every scale — from a laptop in a rural clinic to a GPU cluster in a research hospital.

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    Rare AI Archive Ecosystem                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ Ontology │───▶│ Datasets │───▶│  Models  │───▶│  Deploy  │  │
│  │          │    │          │    │          │    │          │  │
│  │ 4 domains│    │ RareArena│    │ 4-stage  │    │ L1/L2/L3 │  │
│  │ 4K+ dis. │    │ synthetic│    │ pipeline │    │ llama.cpp│  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│       │                               │               │         │
│       │          ┌──────────┐         │               │         │
│       └─────────▶│  Tools   │◀────────┘               │         │
│                  │          │                          │         │
│                  │ ClinVar  │    ┌──────────┐          │         │
│                  │ Orphanet │    │   RLHF   │◀─────────┘         │
│                  │ PanelApp │    │          │                    │
│                  │ gnomAD   │    │ ELO arena│                    │
│                  └──────────┘    │ clinician│                    │
│                                  │ feedback │                    │
│                                  └──────────┘                    │
│                         │                                        │
│                         ▼                                        │
│                  ┌──────────────┐                                │
│                  │  Retrain     │ ◀── Preference data flows     │
│                  │  Loop        │     back to training           │
│                  └──────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

## Architecture

The Archive is built on the [Lattice Protocol](https://github.com/lattice-protocol) standard and organized as a monorepo:

| Package | Purpose |
|---------|---------|
| **[packages/ontology](packages/ontology)** | Disease clustering, clinical tool registry, model/dataset schemas |
| **[packages/models](packages/models)** | 4-stage training pipeline: SFT → Tool-Use → DPO/GRPO → RL |
| **[packages/datasets](packages/datasets)** | RareArena ingestion, synthetic patients, preference data |
| **[packages/rlhf](packages/rlhf)** | Clinician evaluation portal with multi-dimensional ELO |
| **[packages/tools](packages/tools)** | Clinical tool integrations (ClinVar, Orphanet, PanelApp, gnomAD, HPO, PubMed) |
| **[packages/compliance](packages/compliance)** | FAIR scoring, aDNA schema validation, governance |
| **[deploy](deploy)** | Docker Compose overlays for L1/L2 deployment |

## Quick Start

```bash
# Install all packages in development mode
./scripts/setup_dev.sh

# Validate the archive
python scripts/validate_archive.py .
```

## Training Pipeline

We fine-tune [Qwen 3.5](https://huggingface.co/Qwen) models across 4 progressive stages:

| Stage | Method | Data Source | Goal |
|-------|--------|-------------|------|
| 1. SFT | Supervised fine-tuning | RareArena + synthetic cases | Clinical diagnostic reasoning |
| 2. Tool-Use SFT | Agentic traces | Gold-standard tool invocations | ClinVar/Orphanet/PanelApp usage |
| 3. DPO/GRPO | Preference alignment | Clinician evaluations from L2 | Expert-aligned reasoning |
| 4. Progressive RL | Reward optimization | RareArena-derived reward | Top-1 diagnostic accuracy |

**Frameworks:** [Unsloth](https://github.com/unslothai/unsloth) for dense models (QLoRA 4-bit), [Swift](https://github.com/modelscope/ms-swift) for MoE models (bf16 LoRA).

## Model Priority

| Priority | Model | Params | GGUF Size | Deployment Tier |
|----------|-------|--------|-----------|----------------|
| 1 | Qwen3.5-4B | 4B dense | ~3 GB | L1 standard |
| 2 | Qwen3.5-9B | 9B dense | ~6.5 GB | L1 primary |
| 3 | Qwen3.5-27B | 27B dense | ~16 GB | L2 standard |
| 4 | Qwen3.5-35B-A3B | 35B MoE (3B active) | ~20 GB | L2 efficient |

## HuggingFace

Models, datasets, and interactive Spaces are published to the [wilhelm-foundation](https://huggingface.co/wilhelm-foundation) organization on HuggingFace.

## Built on Lattice Protocol

The Rare AI Archive follows the [Lattice Protocol](https://github.com/lattice-protocol) standard:
- **Three primitives:** Dataset, Module, Lattice
- **aDNA metadata:** Embedded agentic DNA for each package
- **Compute tiers:** L1 (edge), L2 (cluster), L3 (datacenter)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to get involved. Whether you're a clinician, ML engineer, bioinformatician, or patient advocate — there's a place for you.

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.

---

*Built by people who believe that no disease is too rare to matter.*
