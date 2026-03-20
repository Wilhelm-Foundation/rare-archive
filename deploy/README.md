# Rare Archive Deploy

Docker Compose deployment overlays for the [Rare AI Archive](https://github.com/Wilhelm-Foundation/rare-archive).

## L2 Deployment (Dell 4x A100-80GB)

### Architecture

```
GPU 3 (A100-80GB) — Dedicated to Archive inference
├── llama-server-primary (port 8082) — Qwen3.5-35B-A3B Q8_0
├── llama-server-arena (port 8083) — Qwen3.5-27B Q8_0
└── (models share GPU via mmap)

Services:
├── OpenWebUI (port 3100) — Clinical interface + Arena mode
├── ChromaDB (port 8084) — RAG vector storage
├── archive-api (port 8085) — ELO tracking + preference export
└── NGINX (/archive/, /elo/) — Reverse proxy
```

### Quick Start

```bash
# 1. Download models
./scripts/download_gguf_models.sh --output-dir /data/latlab/rare-archive/models

# 2. Configure environment
cp deploy/l2/.env.rare-archive deploy/l2/.env
# Edit .env with your secrets

# 3. Deploy (from existing L2 deploy directory)
docker compose -f deploy/l2/docker-compose.rare-archive.yaml --env-file deploy/l2/.env up -d

# 4. Add NGINX location blocks
# Copy deploy/l2/nginx/archive.conf blocks into lattice.conf
# Reload NGINX: docker exec lattice-nginx nginx -s reload
```

### GPU Allocation

| GPU | Allocation |
|-----|-----------|
| 0-2 | Existing L2 workloads (Ray, protein design) |
| 3 | Rare AI Archive inference (dedicated) |

The overlay uses `device_ids: ['3']` to isolate from existing workloads.

> **Port note**: OpenWebUI runs on port 3100 (remapped from default 3000 to avoid memgraph-lab conflict on L2). Ensure port 3100 is free before deploying.

## License

Apache 2.0
