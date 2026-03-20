# Rare Archive Models

4-stage LoRA training pipeline, evaluation harness, and GGUF quantization for the [Rare AI Archive](https://github.com/Wilhelm-Foundation/rare-archive).

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

- **Unsloth**: All model sizes — QLoRA 4-bit for dense, bf16 for MoE
- MoE models require `lora_dropout: 0.0` (ParamWrapper gradient bug) and `TORCHDYNAMO_DISABLE=1`

## Expected Training Times (A100-80GB)

| Model | Steps (3 epochs) | Time/Step | Total | VRAM |
|-------|-------------------|-----------|-------|------|
| 4B dense | ~11,853 | ~7s | ~23h | ~24 GB |
| 9B dense | ~11,853 | ~14s | ~46h | ~40 GB |
| 27B dense | ~11,853 | ~25s | ~82h | ~65 GB |
| 35B MoE | ~11,853 | ~38s | ~128h | ~72 GB |

> Times assume 63,212 training records, batch size 1 × 16 gradient accumulation, `max_seq_length: 4096`.

## Hyperparameter Ranges

| Parameter | 4B | 9B | 27B | 35B MoE |
|-----------|----|----|-----|---------|
| LoRA rank | 64 | 64 | 32 | 32 |
| LoRA alpha | 128 | 128 | 64 | 64 |
| Learning rate | 2e-4 | 2e-4 | 1e-4 | 1e-4 |
| Dropout | 0.05 | 0.05 | 0.05 | 0.0 (required) |
| Batch (effective) | 16 | 16 | 16 | 16 |

## License

Apache 2.0
