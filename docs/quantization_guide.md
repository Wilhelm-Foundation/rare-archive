# Quantization Guide — Rare AI Archive

How to convert fine-tuned LoRA adapters into deployable GGUF files.

## Pipeline

```
LoRA Adapter (~300-400 MB)
    │
    ▼  merge_lora (PEFT merge + unload)
Full Model (~7-70 GB)
    │
    ▼  quantize_gguf (llama.cpp convert + quantize)
GGUF File (~2-40 GB)
    │
    ▼  validate_quant (smoke test)
Verified GGUF
```

## Quant Method Comparison

| Method | Bits | 4B Size | 35B Size | Quality | Use Case |
|--------|------|---------|----------|---------|----------|
| Q8_0 | 8 | 4.2 GB | ~36.9 GB | Highest | L2 serving (max accuracy) |
| Q6_K | 6 | ~3.2 GB | ~28 GB | Very high | L2 memory-constrained |
| Q5_K_M | 5 | ~2.8 GB | ~24 GB | High | L1 primary (best size/quality) |
| Q4_K_M | 4 | ~2.3 GB | ~20 GB | Good | L1 minimum RAM |

**Recommendation**: Q8_0 for L2 (max quality), Q5_K_M for L1 (best tradeoff).

## Step-by-Step

### 1. Merge LoRA into Base Model

```bash
python -m rare_archive_models.quantization.merge_lora \
  --base-model Qwen/Qwen3.5-4B \
  --adapter-path outputs/stage1_sft/lora_adapter \
  --output-path outputs/merged
```

This downloads the base model from HuggingFace, applies the LoRA weights via PEFT, and saves the merged full-precision model. Requires ~2x model size in RAM.

### 2. Convert to GGUF

```bash
python -m rare_archive_models.quantization.quantize_gguf \
  --model-path outputs/merged \
  --output-dir outputs/gguf \
  --method Q8_0 \
  --model-name rare-archive-qwen3.5-4b-sft
```

Output: `outputs/gguf/rare-archive-qwen3.5-4b-sft-Q8_0.gguf`

To produce multiple quant levels:

```bash
for method in Q8_0 Q5_K_M Q4_K_M; do
  python -m rare_archive_models.quantization.quantize_gguf \
    --model-path outputs/merged \
    --output-dir outputs/gguf \
    --method $method \
    --model-name rare-archive-qwen3.5-4b-sft
done
```

### 3. Validate

```bash
python -m rare_archive_models.quantization.validate_quant \
  --gguf-path outputs/gguf/rare-archive-qwen3.5-4b-sft-Q8_0.gguf \
  --quant-method Q8_0
```

Checks file integrity, metadata, and estimated model size.

### 4. Serve with llama-server

```bash
~/Projects/llama.cpp/build/bin/llama-server \
  -m outputs/gguf/rare-archive-qwen3.5-4b-sft-Q8_0.gguf \
  -ngl 99 --port 8082
```

### 5. Publish to HuggingFace

```bash
python scripts/publish_hf.py \
  --gguf-path outputs/gguf/rare-archive-qwen3.5-4b-sft-Q8_0.gguf \
  --repo-id Wilhelm-Foundation/rare-archive-qwen-4b-sft-v1
```

## MoE Considerations (35B-A3B)

- Merged model is ~70 GB — ensure sufficient disk
- Q8_0 output is ~36.9 GB — requires >=48 GB VRAM for full GPU offload
- Use Q5_K_M (~24 GB) for A100-40GB or consumer GPUs
- MoE architecture means only 3B params are active per token, so inference speed is much better than the parameter count suggests

## Troubleshooting

**"Out of memory" during merge**: Reduce `--max-shard-size` or use a machine with more RAM. The 35B merge requires ~80 GB RAM.

**GGUF conversion fails with "unknown architecture"**: Ensure llama.cpp is up to date. Qwen 3.5 support was added in recent releases.

**Quantized model produces gibberish**: Check that the merge step completed successfully. Verify with `validate_quant` before serving.

**Q4_K_M produces poor clinical output**: Expected — use Q5_K_M minimum for clinical applications where reasoning quality matters.
