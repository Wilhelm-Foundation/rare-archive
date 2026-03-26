<p align="center">
  <a href="https://github.com/Wilhelm-Foundation/rare-archive">
    <img src="assets/hero_banner.png" alt="Rare AI Archive" width="100%">
  </a>
</p>

<p align="center">
  <a href="https://github.com/Wilhelm-Foundation/rare-archive/actions/workflows/ci.yaml"><img src="https://github.com/Wilhelm-Foundation/rare-archive/actions/workflows/ci.yaml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License: Apache 2.0"></a>
  <a href="https://huggingface.co/Wilhelm-Foundation"><img src="https://img.shields.io/badge/%F0%9F%A4%97-Models-yellow" alt="HuggingFace"></a>
  <a href="https://huggingface.co/spaces/Wilhelm-Foundation/rare-archive-clinical-demo"><img src="https://img.shields.io/badge/%F0%9F%A7%AC-Clinical_Demo-blue" alt="Demo"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.10%2B-blue" alt="Python 3.10+"></a>
</p>

---

300 million people worldwide live with a rare disease. The average diagnostic odyssey takes 5-7 years. During that time, families navigate a maze of specialists, tests, and uncertainty — often without ever receiving a diagnosis.

**The Rare AI Archive exists to close that gap.**

We are building an open ecosystem for rare disease AI — where patient communities create clinical context, rare disease centers validate it, and open-source model builders turn it into deployed diagnostic tools that improve with every clinician interaction.

*A program of the [Wilhelm Foundation](https://wilhelm.foundation)*

> **Research Use Only.** The Rare AI Archive is a clinical decision support system, not a diagnostic tool. It is **not FDA/CE-cleared** for medical use. All outputs require expert clinical validation and must not be used for autonomous patient care decisions.

### Key Results

- **21.5x improvement** in diagnostic accuracy (Stage 1 SFT — and we're just getting started)
- **69,635 training records** across 9,100 rare diseases
- **7 live clinical tools**: ClinVar, Orphanet, HPO, PanelApp, gnomAD, PubMed, DiffDx
- **Correction-to-retrain cycle** operational end-to-end — clinician feedback improves the system with every interaction

---

## The Ecosystem

The Rare AI Archive is not a single model. It is a **decentralized, collaborative post-training ecosystem** — where the people closest to rare diseases contribute the context that makes AI useful, and the models improve as the community grows.

![Rare AI Archive Ecosystem Flywheel](assets/diagrams/ecosystem_flywheel.png)

Three roles drive the ecosystem:

- **Context Creators** — Patients, families, and clinicians capture structured clinical vignettes — symptom timelines, genetic results, diagnostic journeys — feeding the data that models learn from.
- **Validators** — Rare disease centers, clinical research partners, and patient advocacy organizations validate and curate training data, ensuring clinical accuracy and safety.
- **Model Builders** — Open-source contributors train, fine-tune, and publish condition-specific models on HuggingFace — turning curated data into deployed diagnostic tools.

Each role feeds the next. Patients and clinicians create context. Centers validate it. Community builders turn it into published AI. Clinicians use it, their corrections flow back into training data — and the cycle accelerates.

### Why Open Source Matters

- **Open** — every line of code, every training record, every model weight is inspectable. Rare disease patients deserve visibility, not proprietary lockdown.
- **Federated** — your data never leaves your institution. Models can be fine-tuned locally with your cases.
- **Composable** — built on [aDNA modules](https://github.com/LatticeProtocol) that can be independently improved, replaced, or combined. Swap the base model, add new tools, extend datasets.
- **Deployed** — running on production hardware with 7 live clinical tools, not just a paper.

---

## System Architecture

![Rare AI Archive System Architecture](assets/diagrams/system_overview.png)

> For full architecture diagrams, dependency graphs, and data flow details, see **[ARCHITECTURE.md](ARCHITECTURE.md)**.

## How It Works

```mermaid
graph LR
    O["Ontology<br/>4 domains · 4K+ diseases"] --> D["Datasets<br/>RareArena · synthetic"]
    D --> M["Models<br/>4-stage pipeline"]
    M --> Deploy["Deploy<br/>L1/L2/L3 · llama.cpp"]
    O --> T["Tools<br/>ClinVar · Orphanet<br/>PanelApp · gnomAD"]
    M --> T
    Deploy --> R["RLHF Arena<br/>ELO · clinician feedback"]
    R -->|"preference data"| M
    R -->|"corrections"| D
```

## Quick Start

### Option 1: Try the demo (no install needed)

Visit the **[Clinical Demo Space](https://huggingface.co/spaces/Wilhelm-Foundation/rare-archive-clinical-demo)** — 10 pre-built scenarios covering Gaucher, Duchenne, Fabry, and more.

### Option 2: Run locally with llama.cpp

```bash
# 1. Download the model (~4.2 GB)
pip install huggingface_hub
huggingface-cli download Wilhelm-Foundation/rare-archive-qwen-4b-sft-v1 \
  rare-archive-qwen-4b-sft-v1-Q8_0.gguf \
  --local-dir ~/Models

# 2. Start the inference server (requires llama.cpp — see docs/l1_local_setup.md)
llama-server -m ~/Models/rare-archive-qwen-4b-sft-v1-Q8_0.gguf -ngl 99 --port 8082

# 3. Ask a clinical question
curl http://localhost:8082/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "rare-archive",
    "messages": [{"role": "user", "content": "5-year-old with hepatosplenomegaly, bone pain, and Erlenmeyer flask deformity on X-ray. What rare diseases should I consider?"}],
    "max_tokens": 512
  }'
```

> See the full **[L1 Local Setup Guide](docs/l1_local_setup.md)** for Apple Silicon build instructions and OpenWebUI integration.

### Option 3: Development setup

```bash
# Clone and install all packages in development mode
git clone https://github.com/Wilhelm-Foundation/rare-archive.git
cd rare-archive
./scripts/setup_dev.sh

# Validate the archive
python scripts/validate_archive.py .
```

<details>
<summary><strong>Example Output</strong></summary>

Query: *"8-year-old with progressive proximal muscle weakness, elevated CK, Gower sign positive"*

```
Differential Diagnosis:
1. Duchenne Muscular Dystrophy (DMD) — most likely given age, sex-linked
   inheritance pattern, proximal weakness, and markedly elevated CK
2. Becker Muscular Dystrophy (BMD) — milder variant, later onset possible
3. Limb-Girdle Muscular Dystrophy (LGMD) — autosomal forms to consider

Recommended workups:
- Dystrophin gene (DMD) sequencing via ClinVar [tool: clinvar_lookup]
- HPO phenotype matching for HP:0003236 (elevated CK) [tool: hpo_lookup]
- PanelApp neuromuscular panel review [tool: panelapp_search]
```

</details>

## Architecture

The Archive is built on the [Lattice Protocol](https://github.com/LatticeProtocol) standard and organized as a monorepo:

| Package | Purpose |
|---------|---------|
| **[packages/ontology](packages/ontology)** | Disease clustering, clinical tool registry, model/dataset schemas |
| **[packages/models](packages/models)** | 4-stage training pipeline: SFT → Tool-Use → DPO/GRPO → RL |
| **[packages/datasets](packages/datasets)** | RareArena ingestion, synthetic patients, preference data |
| **[packages/rlhf](packages/rlhf)** | Clinician evaluation portal: multi-dimensional ELO, feedback loops, ChromaDB embeddings |
| **[packages/tools](packages/tools)** | Clinical tool integrations (ClinVar, Orphanet, PanelApp, gnomAD, HPO, PubMed) |
| **[packages/compliance](packages/compliance)** | FAIR scoring, aDNA schema validation, governance |
| **[deploy](deploy)** | Docker Compose overlays for L1/L2 deployment |
| **[docs](docs#readme)** | [11 guides](docs#readme): quantization, evaluation, troubleshooting, tool integration, L1 setup, and more |

## Training Pipeline

We fine-tune [Qwen 3.5](https://huggingface.co/Qwen) models across 4 progressive stages:

| Stage | Method | Data Source | Goal |
|-------|--------|-------------|------|
| 1. SFT | Supervised fine-tuning | RareArena + synthetic cases | Clinical diagnostic reasoning |
| 2. Tool-Use SFT | Agentic traces | Gold-standard tool invocations | ClinVar/Orphanet/PanelApp usage |
| 3. DPO/GRPO | Preference alignment | Clinician evaluations from L2 | Expert-aligned reasoning |
| 4. Progressive RL | Reward optimization | RareArena-derived reward | Top-1 diagnostic accuracy |

**Frameworks:** [Unsloth](https://github.com/unslothai/unsloth) for all model sizes (QLoRA). Dense models use 4-bit quantization; MoE models use bf16 with `lora_dropout=0.0`.

## Models

### Foundation Models

| Priority | Model | Params | GGUF Size | Deployment | Status |
|----------|-------|--------|-----------|------------|--------|
| 1 | [Qwen3.5-4B](https://huggingface.co/Wilhelm-Foundation/rare-archive-qwen-4b-sft-v1) | 4B dense | ~3 GB | L1 standard | **Published** |
| 2 | Qwen3.5-9B | 9B dense | ~6.5 GB | L1 primary | Planned |
| 3 | Qwen3.5-27B | 27B dense | ~16 GB | L2 standard | Planned |
| 4 | Qwen3.5-35B-A3B | 35B MoE (3B active) | ~37 GB | L2 efficient | Training |

### Condition-Specific Models

Specialized models for disease clusters — each trained on domain-specific data and owned by its community:

| Disease Cluster | Diseases | Cases | Foundation | Status |
|----------------|----------|-------|------------|--------|
| **IEM / Lysosomal Storage** | Gaucher, Fabry, Pompe, Niemann-Pick | ~2,400 | Qwen3.5-4B | **Adapter complete** |
| **Neuromuscular Disorders** | Duchenne, SMA, Myasthenia Gravis, CMT | ~300 | Qwen3.5-4B | **Adapter complete** |
| **Connective Tissue** | Ehlers-Danlos, Marfan, Loeys-Dietz | ~1,800 | Qwen3.5-4B | Planned |
| **Autoimmune** | Sjogren's, Systemic Lupus, Scleroderma | ~1,500 | Qwen3.5-4B | Planned |
| **Mitochondrial** | MELAS, Leigh Syndrome, Kearns-Sayre | ~1,000 | Qwen3.5-4B | Planned |

> **Download models:** All published models are available at [huggingface.co/Wilhelm-Foundation](https://huggingface.co/Wilhelm-Foundation) in GGUF format for local inference.

## Roadmap

| Milestone | Focus | Status |
|-----------|-------|--------|
| **Stage 1 SFT** | Supervised fine-tuning on RareArena + synthetic cases | **Complete** — 21.5% Top-1 (21.5x over baseline) |
| **Condition-Specific Models** | IEM and Neuromuscular adapters, then Connective Tissue + Autoimmune | **In progress** — 2 adapters complete |
| **Stage 2 Tool-Use** | Tool-use SFT with gold-standard clinical tool traces | In progress |
| **Community Onboarding** | Templates for disease communities to contribute vignettes and train models | Planned |
| **Rare Disease Leaderboard** | Public benchmark space for comparing diagnostic systems | Planned |
| **Federated Deployment** | Multi-site deployment — hospitals retain data sovereignty | Planned |
| **Stage 3 DPO/GRPO** | Preference alignment from clinician evaluations | Planned |
| **Stage 4 Progressive RL** | Reward optimization with RareArena-derived reward signal | Planned |

## Cite Us

If you use the Rare AI Archive in your research, please cite:

```bibtex
@software{rare_ai_archive_2026,
  title     = {Rare AI Archive: Open-Source Clinical AI for Rare Disease Diagnostics},
  author    = {Wilhelm Foundation and Lattice Protocol},
  year      = {2026},
  url       = {https://github.com/Wilhelm-Foundation/rare-archive},
  license   = {Apache-2.0},
  note      = {A decentralized post-training, model validation, and clinical deployment ecosystem for rare genetic diseases}
}
```

## Community

We welcome contributions from clinicians, ML engineers, bioinformaticians, and patient advocates. Three roles drive the ecosystem:

- **Clinical Validators** — Rare disease specialists who evaluate model outputs, identify errors, and submit corrections that improve the next training run
- **Context Creators** — Clinicians and patient advocates who contribute structured clinical case narratives grounded in lived diagnostic experience
- **Model Builders** — ML engineers who fine-tune condition-specific models using clinician feedback and publish them on HuggingFace

All three roles are essential. See **[CONTRIBUTING.md](CONTRIBUTING.md)** for how to get involved.

- **[GitHub Discussions](https://github.com/Wilhelm-Foundation/rare-archive/discussions)** — questions, ideas, and feedback
- **[Clinical Demo](https://huggingface.co/spaces/Wilhelm-Foundation/rare-archive-clinical-demo)** — try it before you build on it
- **[Complete Toolkit](https://huggingface.co/collections/Wilhelm-Foundation/rare-ai-archive-complete-toolkit-69c4b1e14800a370fe028851)** — model + datasets + demo collection on HuggingFace
- **[Wilhelm Foundation](https://wilhelm.foundation)** — the organization behind this work

## Related Work

We build on and acknowledge outstanding work in rare disease AI:

- **[DeepRare](https://arxiv.org/abs/2501.00070)** (2025) — 57.18% Recall@1 with 40+ tools (closed-source, highest reported performance)
- **[RareBench](https://arxiv.org/abs/2409.04110)** (2024) — benchmarking framework for rare disease diagnosis
- **[Zebra-Llama](https://arxiv.org/abs/2411.02657)** (2024) — focused single-disease LLM for Ehlers-Danlos Syndrome

Our approach is complementary — focused not on one model or one benchmark, but on building the open ecosystem where many models, many communities, and many deployment sites collaborate to make rare disease AI continuously better.

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.

---

*Built by people who believe that no disease is too rare to matter.*
