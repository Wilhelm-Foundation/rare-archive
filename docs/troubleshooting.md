# Troubleshooting — Rare AI Archive

Common issues and their fixes, organized by category.

## Training

### OOM During Training

**Symptom**: `torch.cuda.OutOfMemoryError` or process killed by OOM killer.

**Decision tree**:
1. Check GPU memory: `nvidia-smi`
2. Is another process using the GPU? → Kill it or move to a different GPU
3. Is the model too large for the GPU?
   - 4B: needs ~24 GB (A100-40GB works)
   - 35B MoE: needs ~72 GB (A100-80GB required)
4. Reduce memory:
   - Lower `per_device_train_batch_size` to 1
   - Increase `gradient_accumulation_steps` to compensate
   - Reduce `max_seq_length` (try 2048)
   - Ensure `gradient_checkpointing: true`

### MoE Training Gradient Bugs

**Symptom**: `RuntimeError` in backward pass mentioning `ParamWrapper` or expert routing.

**Fix**: Set `lora_dropout: 0.0` in the config. Nonzero dropout causes gradient computation errors in MoE expert routing layers.

### YAML Learning Rate Parsed as String

**Symptom**: Training fails with type error on learning rate, or LR is unexpectedly 0.

**Fix**: Ensure learning rate uses explicit float notation:
```yaml
# Good
learning_rate: 1e-4

# Bad (may parse as string in some YAML loaders)
learning_rate: 2e-4  # Some loaders interpret this as "2e-4" string
```

If in doubt, use `learning_rate: 0.0001`.

### VL Processor Type Mismatch

**Symptom**: `ValueError: Processor type not recognized` when loading Qwen model.

**Fix**: Qwen 3.5 uses `AutoProcessor`, not `AutoTokenizer` with VL config. Ensure you're using `Qwen3.5-*` (not `Qwen3.5-VL-*`) base models for text-only fine-tuning.

## Deployment

### Port Conflicts

**Symptom**: Container fails to start, `address already in use`.

| Port | Service | Common Conflict |
|------|---------|-----------------|
| 3100 | OpenWebUI | memgraph-lab (default 3000, remapped) |
| 8082 | llama-server primary | JupyterHub proxy |
| 8083 | llama-server arena | — |
| 8084 | ChromaDB | — |
| 8085 | archive-api | — |

**Fix**: Check `ss -tlnp | grep <port>`, then either stop the conflicting service or remap in `docker-compose.rare-archive.yaml`.

### OpenWebUI Shows No Models

**Symptom**: OpenWebUI loads but model dropdown is empty.

**Checklist**:
1. Is llama-server running? `curl http://localhost:8082/v1/models`
2. Is `OPENAI_API_BASE_URLS` set correctly in compose?
3. Check OpenWebUI logs: `docker logs rare-archive-openwebui`

### OpenWebUI First User Blocked

**Symptom**: Cannot create first admin account when `ENABLE_SIGNUP=false`.

**Fix**: Either set `ENABLE_SIGNUP=true` temporarily, or create admin directly via SQLite:
```bash
docker exec -it rare-archive-openwebui sqlite3 /app/backend/data/webui.db
```

### NGINX 502 Bad Gateway

**Symptom**: `/archive/` returns 502.

**Fix**: NGINX starts before OpenWebUI is ready. Either:
1. Wait 30s and retry
2. Add `resolver 127.0.0.11 valid=30s;` to nginx config for deferred DNS resolution
3. Restart nginx after all containers are up: `docker exec lattice-nginx nginx -s reload`

## Model Loading

### GGUF "Unknown Architecture"

**Symptom**: llama-server refuses to load GGUF file.

**Fix**: Update llama.cpp. Qwen 3.5 support requires a recent release. Build from latest:
```bash
cd ~/Projects/llama.cpp && git pull && cmake -B build -DGGML_METAL=ON && cmake --build build --config Release -j$(sysctl -n hw.ncpu)
```

### Slow Generation (No GPU Offload)

**Symptom**: <5 tokens/sec on a machine that should do 20+.

**Fix**: Ensure GPU offload is active:
- **macOS (Metal)**: Check for `ggml_metal_device_init` in startup output. Rebuild with `-DGGML_METAL=ON`.
- **Linux (CUDA)**: Use `-ngl 99` flag. Check `nvidia-smi` shows GPU utilization.

### Model Produces Gibberish

**Symptom**: Output is random tokens or repeated characters.

**Causes**:
1. Corrupted GGUF — re-run quantization, validate with `validate_quant`
2. Wrong chat template — Qwen 3.5 uses ChatML format. Ensure `--chat-template chatml` or let llama-server auto-detect
3. Truncated download — verify file size matches expected (see quantization guide)

## Clinical Tools

### API Rate Limits

**Symptom**: Tool returns empty results or HTTP 429.

| API | Rate Limit | Mitigation |
|-----|-----------|------------|
| NCBI (ClinVar, PubMed) | 3 req/sec (10 with API key) | Set `NCBI_API_KEY` env var |
| Orphanet | ~1 req/sec | Built-in backoff in adapter |
| gnomAD GraphQL | ~5 req/sec | Response caching (1h TTL) |
| PanelApp | ~2 req/sec | Built-in backoff |

### Orphanet API Changed

**Symptom**: Orphanet tool returns 404 or unexpected schema.

**Context**: Orphanet restructured their API in early 2026 from flat endpoints to domain-based endpoints. The adapter was updated in M04. If it breaks again, check the [Orphadata API docs](https://api.orphacode.org/).

### HPO Disease Association Missing

**Symptom**: HPO tool can't find diseases for a phenotype term.

**Context**: HPO removed the term→diseases endpoint. The adapter falls back to Orphanet phenotype-gene associations. If both fail, check that the HPO term ID is valid at [hpo.jax.org](https://hpo.jax.org/).

## Data Pipeline

### filter_category.py Returns 0 Matches

**Symptom**: `Matched 0/63212 records for category 'iem'`

**Fix**: Check that `--input` points to `combined_train.jsonl` (not a split file). Verify the category exists in `CATEGORIES` dict in the script.

### HuggingFace Upload Fails

**Symptom**: `huggingface_hub.utils.HfHubHTTPError: 403`

**Fix**: Ensure you're authenticated (`huggingface-cli login`) and have write access to the `wilhelm-foundation` org. Check that the repo exists on HF first.
