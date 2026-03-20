# GGUF Quality Verification

Procedure for verifying quantized model quality against the full-precision SFT baseline.

## Baseline

| Metric | Value | Source |
|--------|-------|--------|
| Model | Qwen 3.5 35B-A3B — Stage 1 SFT (LoRA) | `outputs/stage1_sft/lora_adapter` |
| Eval set | RareArena RDS (200 cases) | `data/rarearena_eval_rds.jsonl` |
| Top-1 accuracy | 21.5% | Full-precision evaluation |
| Top-5 accuracy | — | (baseline reference) |

## Quantization Targets

| Format | Expected Quality | Acceptable Drop |
|--------|-----------------|-----------------|
| Q8_0 | Near-lossless | <2% Top-1 degradation |
| Q5_K_M | Good quality | <5% Top-1 degradation |
| Q4_K_M | Usable (if needed) | <8% Top-1 degradation |

## Running the Evaluation

### 1. Full-Precision Baseline (if not already captured)

```bash
python scripts/run_eval.py \
    --model Qwen/Qwen3.5-4B \
    --adapter outputs/stage1_sft/lora_adapter \
    --eval-data data/rarearena_eval_rds.jsonl \
    --max-cases 200 \
    --output outputs/eval_sft_rds_200.json
```

### 2. Q8_0 Evaluation

```bash
python scripts/run_eval.py \
    --model models/rare-disease-specialist-q8_0.gguf \
    --eval-data data/rarearena_eval_rds.jsonl \
    --max-cases 200 \
    --output outputs/eval_q8_0_rds_200.json
```

### 3. Q5_K_M Evaluation

```bash
python scripts/run_eval.py \
    --model models/rare-disease-specialist-q5_k_m.gguf \
    --eval-data data/rarearena_eval_rds.jsonl \
    --max-cases 200 \
    --output outputs/eval_q5_k_m_rds_200.json
```

## Results Template

Copy this table into the vault artifact for the mission:

```markdown
| Quantization | Top-1 | Top-5 | Drop vs FP | Status |
|-------------|-------|-------|------------|--------|
| Full-precision (SFT) | 21.5% | —% | — | Baseline |
| Q8_0 | —% | —% | —% | PASS/FAIL |
| Q5_K_M | —% | —% | —% | PASS/FAIL |
```

## Pass/Fail Criteria

- **PASS**: Top-1 drop within acceptable range for quantization level
- **FAIL**: Top-1 drop exceeds threshold — investigate and consider:
  - Re-quantizing with different calibration data
  - Using a higher-quality quantization (e.g., Q6_K instead of Q5_K_M)
  - Checking for quantization artifacts in clinical terminology

## Notes

- Run eval on the same GPU used in production (L2 GPU 3) for timing accuracy
- The eval harness (`scripts/run_eval.py`) uses Unsloth for model loading
- GGUF files are excluded from git (see `.gitignore`) — stored on L2 at `/data/models/`
- Results JSON files go to `outputs/` (also gitignored) — copy key metrics to vault artifact
