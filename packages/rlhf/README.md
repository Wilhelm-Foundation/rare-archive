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

## License

Apache 2.0
