---
title: Rare AI Archive — Clinical Demo
emoji: 🧬
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: "6.9.0"
app_file: app.py
pinned: true
license: apache-2.0
short_description: "Rare disease diagnostics — 10 clinical scenarios"
tags:
  - rare-disease
  - clinical-diagnostics
  - medical-ai
  - lattice-protocol
  - wilhelm-foundation
---

# Rare AI Archive — Clinical Demo

Interactive demonstration of AI-assisted rare disease diagnostics. Explore 10 clinical scenarios with tool-augmented diagnostic reasoning.

## Features

- **10 clinical scenarios** across 6 disease categories (IEM, neuromuscular, connective tissue, immunodeficiency, mitochondrial, complex genetic)
- **7 clinical tool integrations** — Orphanet, ClinVar, gnomAD, PanelApp, HPO, PubMed, DiffDx
- **Structured clinical assessments** with evidence synthesis, management recommendations, and genetic counseling

## Important

- **Research use only** — all patient data is synthetic
- **Not a diagnostic tool** — outputs require clinical validation
- Responses are pre-computed from the Rare Disease Specialist model

## Datasets

- [Synthetic Patients](https://huggingface.co/datasets/Wilhelm-Foundation/rare-archive-synthetic-patients) — 12,984 SFT training vignettes
- [RareArena RDS](https://huggingface.co/datasets/Wilhelm-Foundation/rare-archive-eval-rarearena-rds) — 8,562 evaluation cases
- [RareArena RDC](https://huggingface.co/datasets/Wilhelm-Foundation/rare-archive-eval-rarearena-rdc) — 4,376 cases with lab data

## Links

- [Complete Toolkit Collection](https://huggingface.co/collections/Wilhelm-Foundation/rare-ai-archive-complete-toolkit-69c4b1e14800a370fe028851)
- [GitHub](https://github.com/Wilhelm-Foundation/rare-archive)
- [HuggingFace Organization](https://huggingface.co/Wilhelm-Foundation)
- [4B GGUF Model](https://huggingface.co/Wilhelm-Foundation/rare-archive-qwen-4b-sft-v1)

*A program of the [Wilhelm Foundation](https://wilhelm.foundation). Built on [Lattice Protocol](https://github.com/LatticeProtocol). No disease is too rare to matter.*
