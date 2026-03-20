# Evaluation Metrics — Rare AI Archive

How we measure rare disease diagnostic model performance.

## Core Metrics

### Top-1 Accuracy

The model's first-choice diagnosis matches the ground truth.

```
Top-1 = (# correct first diagnoses) / (# total cases)
```

This is the primary metric. A clinician using the model gets the right answer on the first suggestion.

### Top-5 Accuracy

The ground truth diagnosis appears anywhere in the model's top 5 suggestions.

```
Top-5 = (# cases where ground truth in top 5) / (# total cases)
```

Captures "differential diagnosis" ability — did the model at least consider the correct disease?

### Mean Score

Average semantic similarity between model output and ground truth, scored 0-1. Uses structured field matching across diagnosis name, inheritance pattern, gene associations, and clinical features.

```
Mean = average(similarity_score for each case)
```

Useful for measuring partial credit — a model that says "Gaucher disease type II" when the answer is "Gaucher disease type I" scores higher than one that says "influenza."

## Benchmarks

### RareArena Benchmark

200 held-out evaluation cases across 4 disease categories:

| Category | Cases | Description |
|----------|-------|-------------|
| IEM (Inborn Errors of Metabolism) | ~50 | Enzyme deficiencies, metabolic disorders |
| RDS (Rare Disease Syndromes) | ~80 | Multi-system genetic conditions |
| RDC (Rare Disease Cancer) | ~40 | Rare malignancies with genetic basis |
| NMD (Neuromuscular Disorders) | ~30 | Genetic neuromuscular conditions |

### Running Evaluation

```bash
# Evaluate base model (baseline)
python scripts/run_eval.py \
  --base-model Qwen/Qwen3.5-4B \
  --eval-data data/rarearena_rds_eval.jsonl \
  --output-path outputs/eval/base_4b.json

# Evaluate fine-tuned model
python scripts/run_eval.py \
  --base-model Qwen/Qwen3.5-4B \
  --adapter-path outputs/stage1_sft/lora_adapter \
  --eval-data data/rarearena_rds_eval.jsonl \
  --output-path outputs/eval/sft_4b.json
```

### Output Format

```json
{
  "model": "Qwen/Qwen3.5-4B + LoRA",
  "eval_data": "data/rarearena_rds_eval.jsonl",
  "num_cases": 200,
  "metrics": {
    "top_1_accuracy": 0.215,
    "top_5_accuracy": 0.280,
    "mean_score": 0.620
  },
  "per_category": {
    "iem": {"top_1": 0.24, "top_5": 0.32, "mean": 0.65},
    "rds": {"top_1": 0.20, "top_5": 0.26, "mean": 0.60}
  }
}
```

## Baseline Comparisons

| Model | Top-1 | Top-5 | Mean | Notes |
|-------|-------|-------|------|-------|
| Qwen3.5-4B (base) | 1.0% | 2.5% | 0.089 | Near-random on rare diseases |
| Qwen3.5-4B (SFT v1) | 21.5% | 28.0% | 0.620 | 21.5x improvement, 63K training examples |
| Qwen3.5-35B-A3B (base) | TBD | TBD | TBD | Training in progress (~March 25) |
| Qwen3.5-35B-A3B (SFT) | TBD | TBD | TBD | Expected: 40-50% Top-1 |

## Improvement Thresholds

| Threshold | Metric | Decision |
|-----------|--------|----------|
| > 15% Top-1 | SFT vs base | Publish to HuggingFace |
| > 5% Top-1 delta | Fine-tuned vs base (same size) | Proceed to Stage 2 training |
| > 30% Top-1 | Any model | Production-ready for clinical demo |

## RLHF Arena Metrics

After deployment, models are also rated on 5 ELO dimensions per (model, category):

| Dimension | What it Measures |
|-----------|-----------------|
| Overall | Aggregate Arena win rate |
| Diagnostic Accuracy | Correct diagnosis identification |
| Reasoning Quality | Clinical reasoning chain coherence |
| Tool Usage | Appropriate clinical tool invocations |
| Safety | Avoiding harmful recommendations |

See `packages/rlhf/README.md` for arena API details.
