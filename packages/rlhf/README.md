# Rare Archive RLHF

RLHF portal backend for the [Rare AI Archive](https://github.com/Wilhelm-Foundation/rare-archive). Extends OpenWebUI Arena mode with multi-dimensional ELO tracking, expert matching, preference data export, and clinical correction feedback loops.

For the full system architecture with diagrams, see [ARCHITECTURE.md](../../ARCHITECTURE.md).

## Architecture

```
Expert → JupyterHub SSO → OpenWebUI Arena
                               │
                    ┌──────────┴──────────┐
                    │                     │
              Model A Response     Model B Response
                    │                     │
                    └──────────┬──────────┘
                               │
                    Expert Selects Winner +
                    Structured Annotations
                               │
                          archive-api
                    ┌──────────┴──────────┐
                    │                     │
              ELO Update           Preference Pair
              (per category,       (DPO-compatible)
               per dimension)            │
                    │               HuggingFace
                    │               Export (append + dedup)
                    │
         Correction Feedback
                    │
          ┌────────┴────────┐
          │                 │
     PostgreSQL         ChromaDB
     (primary)       (embeddings)
          │                 │
     SFT Export      Semantic Search
     (JSONL)         (RAG retrieval)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/elo/ratings` | GET | All model ratings |
| `/elo/ratings/{model_id}` | GET | Ratings for a model |
| `/elo/update` | POST | Update ELO after comparison |
| `/experts/register` | POST | Register clinical expert |
| `/experts/match/{category}` | GET | Match experts to category |
| `/evaluations/submit` | POST | Submit Arena evaluation |
| `/evaluations/stats` | GET | Evaluation statistics |
| `/preferences/pairs` | GET | Extract DPO preference pairs |
| `/preferences/export` | POST | Export to HuggingFace (append + dedup) |
| `/cases/create` | POST | Add a clinical case |
| `/cases/batch` | POST | Batch insert (skip duplicates) |
| `/cases/{case_id}` | GET | Retrieve case by ID |
| `/cases/random/pick` | GET | Random case (optional category) |
| `/cases/` | GET | List with pagination |
| `/feedback/correction` | POST | Submit correction → PostgreSQL + ChromaDB |
| `/feedback/annotation` | POST | Submit free-text annotation |
| `/feedback/corrections/search` | GET | Semantic search via ChromaDB |
| `/feedback/corrections/{case_id}` | GET | Get corrections for a case |
| `/feedback/export-training` | GET | Export corrections as SFT JSONL |
| `/feedback/stats` | GET | Feedback counts by type + severity |

## Quick Start

```bash
# Local development
pip install -e ".[dev]"
uvicorn archive_api.main:app --reload

# Docker
docker build -t rare-archive-api src/archive_api/
docker run -p 8085:8000 rare-archive-api
```

## ELO Dimensions

Each model is rated across 5 dimensions per (model, category, mode):
- **Overall** — Aggregate ELO from Arena wins/losses
- **Diagnostic Accuracy** — Correct diagnosis identification
- **Reasoning Quality** — Clinical reasoning chain quality
- **Tool Usage** — Appropriate use of diagnostic tools
- **Safety** — Avoiding harmful recommendations

## ELO Formula

Standard ELO with K-factor adjustment for clinical evaluation:

```
Expected(A) = 1 / (1 + 10^((R_B - R_A) / 400))
New_R_A = R_A + K * (S_A - Expected(A))
```

Where:
- `R_A`, `R_B` = current ratings for models A and B
- `K = 32` (default, higher for new models with few evaluations)
- `S_A = 1.0` (win), `0.5` (tie), `0.0` (loss)
- Starting rating: 1500 per (model, category, dimension)

## Arena Mode Setup

1. Deploy two models on separate llama-server instances (ports 8082, 8083)
2. Configure OpenWebUI Arena mode: `ENABLE_ARENA_MODEL=true`
3. Register models via archive-api: `POST /elo/ratings` with model metadata
4. Experts see blind A/B comparisons, select winner + annotate dimensions

## Preference Data Export

Evaluation results export as DPO-compatible preference pairs:

```json
{
  "prompt": "Clinical vignette text...",
  "chosen": "Model A response (winner)...",
  "rejected": "Model B response (loser)...",
  "metadata": {
    "category": "iem",
    "expert_id": "expert_001",
    "dimensions": {"accuracy": "A", "reasoning": "A", "safety": "tie"}
  }
}
```

Export to HuggingFace: `POST /preferences/export`. Uses append-only logic — downloads existing dataset, deduplicates by `evaluation_id`, appends new pairs, uploads merged file to stable path `data/preferences.jsonl`.

## ChromaDB Integration

Clinical corrections are stored in both PostgreSQL (primary record) and ChromaDB (semantic embeddings) for RAG-style retrieval:

- **Collection**: `clinical_corrections`
- **Embedding model**: all-MiniLM-L6-v2 (via `chromadb==0.5.23`)
- **Store**: `POST /feedback/correction` dual-writes (ChromaDB is best-effort — failures don't block the request)
- **Search**: `GET /feedback/corrections/search?query=Gaucher disease` returns semantically similar corrections
- **Config**: `CHROMADB_URL` env var (default: `http://rare-archive-chromadb:8000`)

## Correction → Retrain Cycle

Corrections can be exported as SFT training data and merged into the next fine-tuning run:

1. Expert submits correction: `POST /feedback/correction`
2. Correction stored in PostgreSQL + ChromaDB
3. Export as JSONL: `GET /feedback/export-training` (system/user/assistant chat format)
4. Merge with existing training data (69,635 records)
5. Run SFT with Unsloth QLoRA
6. Deploy improved GGUF model to llama.cpp

See [ARCHITECTURE.md](../../ARCHITECTURE.md) for detailed diagrams.

## License

Apache 2.0
