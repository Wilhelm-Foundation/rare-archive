# Rare Archive Models

4-stage LoRA training pipeline, evaluation harness, and GGUF quantization for the [Rare AI Archive](https://github.com/wilhelm-foundation/rare-ai-archive).

## Training Pipeline

| Stage | Method | Script | Data |
|-------|--------|--------|------|
| 1 | SFT | `training/stage1_sft.py` | RareArena + synthetic |
| 2 | Tool-Use SFT | `training/stage2_tool_use.py` | Gold-standard traces |
| 3 | DPO/GRPO | `training/stage3_dpo.py` | Clinician preferences |
| 4 | Progressive RL | `training/stage4_rl.py` | RareArena reward |

## Quick Start

```bash
# Stage 1 SFT on Qwen3.5-4B
python -m rare_archive_models.training.stage1_sft \
  --base-config configs/base/4b.yaml \
  --config configs/stages/stage1_sft.yaml

# Evaluate on RareArena
python -m rare_archive_models.evaluation.rarearena_eval \
  --model outputs/stage1_sft/lora_adapter \
  --eval-data data/rarearena_rds_eval.jsonl

# Quantize to GGUF
python -m rare_archive_models.quantization.merge_lora \
  --base-model Qwen/Qwen3.5-4B --adapter-path outputs/stage1_sft/lora_adapter \
  --output-path outputs/merged
python -m rare_archive_models.quantization.quantize_gguf \
  --model-path outputs/merged --output-dir outputs/gguf \
  --method Q5_K_M --model-name rare-archive-qwen3.5-4b-sft
python -m rare_archive_models.quantization.validate_quant \
  --gguf-path outputs/gguf/rare-archive-qwen3.5-4b-sft-Q5_K_M.gguf \
  --quant-method Q5_K_M
```

## Config Hierarchy

```
configs/base/{size}.yaml         # Model-specific (LoRA rank, batch size, etc.)
  -> configs/stages/{stage}.yaml  # Stage-specific (epochs, data paths)
    -> configs/categories/{cat}.yaml  # Category-specific overrides
```

## Frameworks

- **Unsloth**: Dense models (0.8B-27B), QLoRA 4-bit
- **Swift**: MoE models (35B-A3B, 122B-A10B), bf16 LoRA

## License

Apache 2.0
