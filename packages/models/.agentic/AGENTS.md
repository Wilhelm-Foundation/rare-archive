# Rare Archive Models — Agentic DNA

## Purpose
4-stage LoRA training pipeline, evaluation harnesses, and GGUF quantization for rare disease diagnostic models.

## Training Pipeline
| Stage | Method | Framework |
|-------|--------|-----------|
| 1. SFT | Clinical diagnostic reasoning | Unsloth (dense) |
| 2. Tool-Use SFT | Agentic tool invocation | Unsloth (dense) |
| 3. DPO/GRPO | Clinician preference alignment | Swift (MoE) |
| 4. Progressive RL | RareArena-derived reward | Swift (MoE) |

## Key Directories
- `configs/`: Hierarchical config system (base/{size} → stages/{stage} → categories/{category})
- `src/rare_archive_models/training/`: Stage 1-4 training scripts
- `src/rare_archive_models/evaluation/`: RareArena eval runner
- `src/rare_archive_models/quantization/`: merge_lora.py → quantize_gguf.py → validate_quant.py
