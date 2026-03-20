# Rare Archive RLHF

RLHF portal backend for the [Rare AI Archive](https://github.com/wilhelm-foundation/rare-ai-archive). Extends OpenWebUI Arena mode with multi-dimensional ELO tracking, expert matching, and preference data export.

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
                                    HuggingFace
                                    Export
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
| `/preferences/export` | POST | Export to HuggingFace |

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

Export to HuggingFace: `POST /preferences/export` with `repo_id` and `split` parameters.

## License

Apache 2.0
