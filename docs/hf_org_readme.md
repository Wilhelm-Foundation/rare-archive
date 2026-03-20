# Wilhelm Foundation — AI for Rare Disease Diagnostics

300 million people worldwide live with a rare disease. The average diagnostic odyssey takes 5–7 years. During that time, families navigate a maze of specialists, tests, and uncertainty — often without ever receiving a diagnosis.

**We build open-source AI models specialized in rare disease diagnostics**, validated by clinicians, and deployable at every scale — from a laptop in a rural clinic to a GPU cluster in a research hospital.

## Available Models

| Model | Parameters | Status | Use Case |
|-------|-----------|--------|----------|
| [rare-archive-qwen-4b-sft-v1](https://huggingface.co/Wilhelm-Foundation/rare-archive-qwen-4b-sft-v1) | 4B dense | **Published** (GGUF Q8_0) | Local inference on laptop/edge |
| rare-archive-qwen-35b-a3b-sft | 35B MoE (3B active) | Training in progress | Research hospital / GPU cluster |

**Key result**: 4B SFT achieves 21.5% Top-1 diagnostic accuracy — a 21.5x improvement over the base model on rare disease clinical vignettes.

## Datasets

| Dataset | Records | Description |
|---------|---------|-------------|
| [RareArena](https://huggingface.co/datasets/Wilhelm-Foundation/rare-arena) | 63,212 | Clinical vignettes across 4 disease categories |
| [rare-archive-synthetic-patients](https://huggingface.co/datasets/Wilhelm-Foundation/rare-archive-synthetic-patients) | 5,000+ | Synthetic patient presentations for training |
| [rare-archive-preference](https://huggingface.co/datasets/Wilhelm-Foundation/rare-archive-preference) | — | Clinician preference data for RLHF (collecting) |

## Clinical Tool Pipeline

Our models are augmented with 7 live clinical tool adapters:

- **Orphanet** — Disease information, prevalence, genetics
- **ClinVar** — Variant pathogenicity classification
- **gnomAD** — Population allele frequencies
- **PanelApp** — Gene panels for suspected conditions
- **HPO** — Human Phenotype Ontology mapping
- **PubMed** — Literature search for diagnosis and management
- **DiffDx** — Structured differential diagnosis

## Architecture

```
Ontology (4 domains · 4K+ diseases) → Datasets (RareArena · synthetic)
    ↓                                       ↓
Clinical Tools (7 adapters)          Models (4-stage pipeline)
    ↓                                       ↓
                    Deploy (L1/L2/L3)
                         ↓
                  RLHF Arena (ELO · clinician feedback)
```

**Training pipeline**: SFT → Tool-Use SFT → DPO/GRPO → Progressive RL

**Frameworks**: [Unsloth](https://github.com/unslothai/unsloth) + QLoRA for all model sizes

## Interactive Demo

Try the clinical demo: [**Rare AI Archive Clinical Demo**](https://huggingface.co/spaces/Wilhelm-Foundation/rare-archive-clinical-demo) — explore 10 clinical scenarios with tool-augmented diagnostic reasoning. No account required.

## Links

- **GitHub**: [Wilhelm-Foundation/rare-archive](https://github.com/Wilhelm-Foundation/rare-archive)
- **Documentation**: [Quantization](https://github.com/Wilhelm-Foundation/rare-archive/blob/main/docs/quantization_guide.md) · [Evaluation](https://github.com/Wilhelm-Foundation/rare-archive/blob/main/docs/evaluation_metrics.md) · [Tool Integration](https://github.com/Wilhelm-Foundation/rare-archive/blob/main/docs/tool_integration_spec.md)
- **License**: Apache 2.0

## Built on Lattice Protocol

The Rare AI Archive follows the [Lattice Protocol](https://github.com/LatticeProtocol) standard — three primitives (Dataset, Module, Lattice), aDNA metadata, and compute tier deployment (L1 edge → L2 cluster → L3 datacenter).

---

*Built by people who believe that no disease is too rare to matter.*
