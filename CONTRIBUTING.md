# Contributing to the Rare AI Archive

The Rare AI Archive is a **decentralized post-training ecosystem** for rare disease diagnostics. Three roles drive it — and there is a place for you in each.

Whether you're a clinician who knows rare diseases intimately, an ML engineer who can train models, or a patient advocate who has lived the diagnostic odyssey — your expertise is what makes this system work. The model is one component; the community is the engine.

---

## Ecosystem Roles

### Context Creators

**Who**: Clinicians, geneticists, patient advocates, rare disease families

**What you contribute**: The clinical context that makes AI useful — the reasoning patterns, phenotype-gene mappings, and diagnostic workflows that exist in expert minds but not yet in training data.

**How to get involved**:
- **Undiagnosed Patient Hackathons** — Structured events where specialists reason through the hardest cases together, producing the exact diagnostic workflow traces that train agentic systems. [Learn more](https://www.nature.com/articles/d41586-026-00302-8) | [Watch](https://youtu.be/zPGp0gqTYbo)
- **Clinical vignettes** — Submit structured case descriptions (symptoms, timeline, genetic results, diagnostic journey) through the contribution templates
- **Phenotype-gene mappings** — Validated links between clinical features and genetic variants, curated from published literature

> All contributions use synthetic or published data. No real patient data (PHI) is ever collected, stored, or transmitted.

### Validators

**Who**: Rare disease centers, specialist clinicians, clinical geneticists

**What you contribute**: The quality signal that determines when a model is ready for patients. Your expertise is the final gate between a trained model and clinical deployment.

**How to get involved**:
- **Arena evaluation** — In blind A/B comparisons, you evaluate two model outputs side-by-side across 5 quality dimensions (Diagnostic Accuracy, Reasoning Quality, Tool Usage, Safety, Overall). Your ratings produce multi-dimensional ELO scores that reveal exactly where models excel and where they need improvement.
- **Correction submission** — When you identify a diagnostic error, submit a correction through the Arena interface. Your correction enters the **correction-to-retrain loop**: stored in the feedback database, exported as training data, and incorporated into the next model version.
- **Dataset validation** — Review training data for clinical accuracy, flag cases with questionable reasoning, and validate that synthetic vignettes reflect real diagnostic patterns.

> See [ARCHITECTURE.md](ARCHITECTURE.md) for details on the RLHF feedback loop and correction-to-retrain cycle.

### Model Builders

**Who**: ML engineers, bioinformaticians, software engineers

**What you contribute**: The technical infrastructure that turns clinical expertise into deployed diagnostic tools — training pipelines, tool integrations, evaluation harnesses, and deployment automation.

**How to get involved**:
- **Condition-specific adapters** — Train LoRA adapters for disease clusters (IEM, Neuromuscular, Connective Tissue, etc.) using the existing pipeline in `packages/models/`
- **Tool integrations** — Build new clinical tool adapters (see `packages/tools/` and [tool_integration_spec.md](docs/tool_integration_spec.md))
- **Evaluation harnesses** — Improve RareArena benchmarking, add new evaluation dimensions (see `packages/models/` and [evaluation_metrics.md](docs/evaluation_metrics.md))
- **Quantization and deployment** — Optimize GGUF quantization for edge deployment (see [quantization_guide.md](docs/quantization_guide.md))
- **Infrastructure** — Improve Docker Compose overlays, monitoring, and federated deployment patterns (see `deploy/`)

---

## Contributing Context Files

Context files capture **how experts reason** with clinical tools — the tacit knowledge that makes rare disease specialists effective. This is different from clinical vignettes (cases to reason about) or tool documentation (what tools do). Context files capture the "why" behind each tool invocation and the interpretation rules that come from clinical experience.

### Why Context Matters

When a specialist at the Undiagnosed Patient Hackathon says "I'm checking gnomAD for the Ashkenazi Jewish subpopulation frequency, not the overall frequency" — that's expert reasoning that an AI system needs to learn. Context files make this reasoning structured, versioned, and machine-readable.

Context feeds into three systems:
1. **Runtime grounding** — OpenWebUI injects relevant context during tool-augmented inference
2. **Training annotation** — gold-standard agentic traces reference context to explain tool selection
3. **Evaluation criteria** — the RLHF Arena's "Tool Usage" dimension references context-defined patterns

### The 6 Context Categories

| Category | What to Write | Example |
|----------|--------------|---------|
| `diagnostic_workflow` | Step-by-step reasoning sequence | "For suspected Gaucher: Orphanet → ClinVar → gnomAD (ASJ) → HPO → PubMed" |
| `interpretation_guide` | How to read tool outputs | "N370S homozygous in GBA = Type 1 only; compound het with L444P = higher Type 2/3 risk" |
| `data_source_guide` | Which databases matter and why | "Oxford Nanopore long-read sequencing: when to order, how to interpret SV calls" |
| `tool_sequence` | Tool invocation order with branching | "If ClinVar returns VUS, check gnomAD frequency before escalating to PubMed" |
| `phenotype_pattern` | Clinical feature clusters | "Joint hypermobility + skin elasticity + vascular fragility → COL5A1/COL3A1 panels" |
| `diagnostic_odyssey` | Patient journey lessons | "Average 7-year odyssey for LSD; most common misdiagnosis is hematologic malignancy" |

### How to Contribute a Context File

1. **Start from an exemplar** — see `packages/ontology/context/` for working examples
2. **Use the schema** — all files validate against `packages/ontology/schemas/context_file.schema.json`
3. **Name it correctly** — `rare_ctx_[category]_[disease]_[descriptor].yaml`
4. **Include required fields** — `context_id`, `title`, `version`, `category`, `description`, `when_to_use`
5. **Reference tools by ID** — use `rare_tool_clinvar`, `rare_tool_orphanet`, etc. in `tool_connections` and `workflow_steps`
6. **Add FAIR metadata** — `fair.keywords` (min 3), `fair.license`, `fair.creators`
7. **Submit a PR** — context files go through clinical review (2+ specialists) before publication

### Quality Tiers

New context files enter as `draft`. They progress through `reviewed` → `validated` → `published` as they pass clinical accuracy review, schema validation, and novelty assessment.

---

## Getting Started

### 1. Set Up Your Environment

```bash
git clone https://github.com/Wilhelm-Foundation/rare-archive.git
cd rare-archive
./scripts/setup_dev.sh     # Installs all packages in development mode
```

### Prerequisites

- Python 3.11 or 3.12
- For **training** (`packages/models/`): Linux with NVIDIA GPU, CUDA 12+, PyTorch 2.x
- For **tools** (`packages/tools/`): Internet access for live API testing
- For **deployment** (`deploy/`): Docker Compose v2

### 2. Pick Your Entry Point

| If you are a... | Start with | Key docs |
|----------------|-----------|----------|
| **Clinician** | [Clinical Demo Space](https://huggingface.co/spaces/Wilhelm-Foundation/rare-archive-clinical-demo) — try it first | [demo_scenarios.md](docs/demo_scenarios.md) |
| **ML engineer** | `packages/models/` — training pipeline | [evaluation_metrics.md](docs/evaluation_metrics.md), [quantization_guide.md](docs/quantization_guide.md) |
| **Bioinformatician** | `packages/ontology/` or `packages/tools/` | [tool_integration_spec.md](docs/tool_integration_spec.md) |
| **Software engineer** | `packages/rlhf/` or `deploy/` | [ARCHITECTURE.md](ARCHITECTURE.md), [l1_local_setup.md](docs/l1_local_setup.md) |
| **Patient advocate** | [GitHub Discussions](https://github.com/Wilhelm-Foundation/rare-archive/discussions) | [README.md](README.md) |

### 3. Find Work

- Look for issues labeled **`good-first-issue`**
- Browse [GitHub Discussions](https://github.com/Wilhelm-Foundation/rare-archive/discussions) for open questions
- Check individual package READMEs for known gaps and planned work

---

## Development Guidelines

- **Naming**: Follow [Lattice Protocol conventions](https://github.com/LatticeProtocol) — underscores for files (`stage1_sft.py`), hyphens for HuggingFace-facing names (`rare-archive-qwen-4b-sft-v1`)
- **Testing**: Write tests for new functionality. Run `pytest` from the package directory.
- **No PHI**: Synthetic patients only. Never include real patient data in code, tests, or documentation.
- **Validate**: Run `python scripts/validate_archive.py .` before submitting to check aDNA compliance and FAIR scoring.

### Pull Request Process

1. Fork the repository and create a feature branch
2. Make your changes with tests
3. Run validation: `python scripts/validate_archive.py .`
4. Submit a PR with a clear description of what changed and why
5. A maintainer will review — expect feedback within a few days

---

## Code of Conduct

We are committed to providing a welcoming and inclusive experience for everyone. Rare disease communities are small and deeply personal — the people building this system often include patients and families who live with these conditions. Be kind, be patient, be constructive.

---

<p align="center"><em>No disease is too rare to matter.</em></p>
