# Rare Archive Deploy — Agentic DNA

## Purpose
Docker Compose overlays for L1/L2 deployment of the Rare AI Archive inference stack.

## L2 Deployment
- Docker Compose overlay extends existing lattice-l2 network
- GPU 3 (A100-80GB) dedicated to inference
- Two llama-server instances: primary (35B-A3B Q8_0, 8082) and arena challenger (27B Q8_0, 8083)
- OpenWebUI (3000→8080): Arena mode, clinical tools, RAG
- ChromaDB for RAG vector storage
- archive-api FastAPI sidecar for ELO tracking

## Key Directories
- `deploy/l2/`: docker-compose.rare-archive.yaml, environment configs
- `deploy/l2/nginx/`: NGINX location blocks for /archive/ and /elo/
- `scripts/`: download_gguf_models.sh, deployment helpers
- `catalog/`: catalog.json with model checksums
