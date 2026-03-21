# Architecture

A technical overview of the Rare AI Archive system — its packages, data flows, and external integrations.

![Architecture Overview](docs/images/architecture_overview.png)

## System Overview

The Archive is a monorepo of 6 Python packages that form a pipeline from disease ontology through model training to clinical deployment with feedback.

```mermaid
graph TB
    subgraph "Tier 0 — Foundation"
        ONT["<b>ontology</b><br/>Disease clustering · schemas<br/>4 domains · 9,100 diseases"]
        COMP["<b>compliance</b><br/>aDNA validation · FAIR scoring"]
    end

    subgraph "Tier 1 — Data & Tools"
        DS["<b>datasets</b><br/>RareArena ingestion<br/>Synthetic generation<br/>69,635 training records"]
        TOOLS["<b>tools</b><br/>7 clinical adapters<br/>ClinVar · Orphanet · HPO<br/>PanelApp · gnomAD · PubMed · DiffDx"]
    end

    subgraph "Tier 2 — Training"
        MOD["<b>models</b><br/>4-stage pipeline<br/>SFT → Tool-Use → DPO → RL"]
    end

    subgraph "Tier 3 — Deployment & Feedback"
        RLHF["<b>rlhf</b><br/>Archive API · ELO<br/>Feedback · Preferences"]
    end

    ONT --> DS
    ONT --> TOOLS
    DS --> MOD
    MOD --> RLHF
    COMP -.->|validates| DS
    COMP -.->|validates| MOD

    subgraph "External Services"
        PG[(PostgreSQL)]
        REDIS[(Redis)]
        CHROMA[(ChromaDB<br/>all-MiniLM-L6-v2)]
        HF[🤗 HuggingFace Hub]
        LLAMA[llama.cpp<br/>GPU inference]
        OWUI[OpenWebUI<br/>Arena mode]
    end

    RLHF --> PG
    RLHF --> REDIS
    RLHF --> CHROMA
    RLHF --> HF
    LLAMA --> OWUI
    TOOLS --> OWUI
    OWUI --> RLHF
```

## RLHF Feedback Loop

Clinical experts evaluate model responses in blind A/B comparisons through OpenWebUI's Arena mode. Evaluations drive multi-dimensional ELO ratings and produce DPO-compatible preference data for training.

```mermaid
graph LR
    EXP["👩‍⚕️ Expert<br/>Clinician"] --> ARENA["OpenWebUI<br/>Arena Mode<br/>(blind A/B)"]
    ARENA --> EVAL["Evaluation<br/>Winner + 4-dim<br/>annotations (0-5)"]
    EVAL --> ELO["ELO Update<br/>5 dimensions<br/>per category"]
    EVAL --> PREF["Preference Pair<br/>(chosen/rejected)"]
    PREF --> EXPORT["HF Export<br/>append + dedup<br/>by evaluation_id"]
    EXPORT --> HF["🤗 HuggingFace<br/>Preference Dataset"]
    HF --> TRAIN["Stage 3<br/>DPO / GRPO"]
    TRAIN --> DEPLOY["Deploy<br/>GGUF → llama.cpp"]
    DEPLOY --> ARENA

    style EXP fill:#e1f5fe
    style HF fill:#fff3e0
    style DEPLOY fill:#e8f5e9
```

![RLHF Feedback Loop](docs/images/rlhf_feedback_loop.png)

**ELO Dimensions**: Overall, Diagnostic Accuracy, Reasoning Quality, Tool Usage, Safety — each tracked per model, per disease category, per evaluation mode. K-factor: 32, initial rating: 1500.

## Correction → Retrain Cycle

When an expert identifies a diagnostic error, the correction flows through dual storage (PostgreSQL + ChromaDB) into training data and back into an improved model.

```mermaid
graph TD
    CORR["👩‍⚕️ Expert submits correction<br/>POST /feedback/correction"] --> PG["PostgreSQL<br/>(primary record)"]
    CORR --> CHROMA["ChromaDB<br/>(semantic embeddings<br/>all-MiniLM-L6-v2)"]
    CHROMA --> SEARCH["Semantic Search<br/>GET /corrections/search<br/>(RAG retrieval)"]
    PG --> EXPORT["Export SFT JSONL<br/>GET /feedback/export-training"]
    EXPORT --> MERGE["Merge with<br/>existing 69,635 records"]
    MERGE --> SFT["SFT Training<br/>Unsloth QLoRA<br/>(Qwen3.5-4B)"]
    SFT --> MODEL["Improved Model<br/>GGUF → llama.cpp"]

    style CORR fill:#e1f5fe
    style MODEL fill:#e8f5e9
```

![Correction→Retrain Cycle](docs/images/correction_retrain_cycle.png)

**SFT Format**: Each correction exports as a chat-format JSONL record with `system` (diagnostician prompt), `user` (case vignette), and `assistant` (corrected diagnosis + reasoning). This matches the existing training data format for seamless merging.

## Data Flow

```mermaid
graph LR
    CASES["Case Library<br/>201 cases<br/>9,100 diseases"] --> OWUI["OpenWebUI<br/>Arena"]
    OWUI --> EVAL["Expert<br/>Evaluations"]
    EVAL --> PREF["DPO Preferences<br/>(chosen/rejected)"]
    EVAL --> FB["Clinical<br/>Corrections"]
    PREF --> HF_PREF["🤗 Preference<br/>Dataset"]
    FB --> CHROMA_DB["ChromaDB<br/>Embeddings"]
    FB --> JSONL["SFT Training<br/>JSONL"]
    HF_PREF --> S3["Stage 3<br/>DPO/GRPO"]
    JSONL --> S1["Stage 1<br/>SFT Retrain"]

    style CASES fill:#f3e5f5
    style S3 fill:#e8f5e9
    style S1 fill:#e8f5e9
```

## Archive API

The RLHF backend (`packages/rlhf/src/archive_api/`) is a FastAPI application with 6 routers:

### Endpoints

| Router | Endpoint | Method | Description |
|--------|----------|--------|-------------|
| **elo** | `/elo/ratings` | GET | All model ratings (filterable by category) |
| | `/elo/ratings/{model_id}` | GET | Ratings for a model across categories |
| | `/elo/update` | POST | Update ELO after comparison |
| **experts** | `/experts/register` | POST | Register clinical expert |
| | `/experts/` | GET | List active experts |
| | `/experts/match/{category}` | GET | Match experts to disease category |
| **evaluations** | `/evaluations/submit` | POST | Submit Arena evaluation + trigger ELO |
| | `/evaluations/stats` | GET | Evaluation counts by category |
| **preferences** | `/preferences/pairs` | GET | Extract DPO preference pairs |
| | `/preferences/export` | POST | Export to HuggingFace (append + dedup) |
| **cases** | `/cases/create` | POST | Add a clinical case |
| | `/cases/batch` | POST | Batch insert (skip duplicates) |
| | `/cases/{case_id}` | GET | Retrieve case by ID |
| | `/cases/random/pick` | GET | Random case (optional category filter) |
| | `/cases/` | GET | List with pagination |
| **feedback** | `/feedback/correction` | POST | Submit correction → PostgreSQL + ChromaDB |
| | `/feedback/annotation` | POST | Submit free-text annotation |
| | `/feedback/corrections/search` | GET | Semantic search via ChromaDB |
| | `/feedback/corrections/{case_id}` | GET | Get corrections for a case |
| | `/feedback/export-training` | GET | Export corrections as SFT JSONL |
| | `/feedback/stats` | GET | Feedback counts by type + severity |
| **root** | `/health` | GET | Health check |

### Database Models

| Model | Key Fields | Purpose |
|-------|-----------|---------|
| **Expert** | username, subspecialty, patient_categories | Registered clinical evaluators |
| **ModelRating** | model_id, category, 5× ELO dimensions | Multi-dimensional ELO per model per category |
| **Evaluation** | expert_id, case_id, winner, annotations | Arena comparison records |
| **Case** | case_id, category, vignette, known_diagnosis | Clinical case library |
| **ClinicalFeedback** | case_id, feedback_type, corrected_diagnosis | Corrections, annotations, suggestions |
| **PreferenceExport** | export_date, evaluation_count, hf_commit | HuggingFace export tracking |

## Infrastructure

Deployed on L2 (4× A100-80GB) via Docker Compose:

| Container | Port | Purpose |
|-----------|------|---------|
| `rare-archive-llama-primary` | 8082 | Qwen3.5-35B-A3B inference (GPU 3) |
| `rare-archive-llama-arena` | 8083 | 4B SFT challenger (GPU 3) |
| `rare-archive-openwebui` | 3100 | Clinical interface + Arena mode |
| `rare-archive-chromadb` | 8084 | Vector storage (v0.5.23) |
| `rare-archive-api` | 8085 | Archive API (FastAPI) |
| `lattice-postgres` | 5432 | Shared PostgreSQL |
| `lattice-redis` | 6379 | Shared Redis |
| `lattice-prometheus` | 9090 | Metrics collection |
| `lattice-grafana` | 3000 | Dashboards (via NGINX at `/grafana/`) |

All containers on the `lattice-l2` Docker network. NGINX reverse proxy at port 8000.

## Configuration

Environment variables for the Archive API (`config.py`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://...localhost:5432/rare_archive` | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379/2` | Redis cache |
| `CHROMADB_URL` | `http://rare-archive-chromadb:8000` | ChromaDB server |
| `HF_TOKEN` | — | HuggingFace API token |
| `HF_ORG` | `wilhelm-foundation` | HuggingFace organization |
| `HF_DATASET` | `rare-archive-rlhf-preferences` | Preference dataset name |
| `ELO_K_FACTOR` | `32` | ELO K-factor |
| `ELO_INITIAL_RATING` | `1500` | Starting ELO for new models |
