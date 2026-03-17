# Rare AI Archive — Agentic DNA

## Purpose
Meta-repository and front door for the Rare AI Archive: a decentralized post-training, model validation, and clinical deployment ecosystem for rare genetic diseases.

## Triad Structure
- **what/**: Domain knowledge — ontology context, architecture specs, ADRs
- **how/**: Operations — campaign plans, session tracking, templates
- **who/**: Organization — governance policies, team coordination

## Related Repositories
| Repo | Purpose |
|------|---------|
| rare-archive-ontology | 4 ontology domains, JSON-LD schemas, clustering |
| rare-archive-models | LoRA training pipelines, eval harnesses, GGUF quantization |
| rare-archive-datasets | RareArena ingestion, synthetic patients, preference data |
| rare-archive-rlhf | RLHF portal, ELO system, expert matching |
| rare-archive-tool-harness | Clinical tool-use harness (ClinVar, Orphanet, PanelApp, etc.) |
| rare-archive-deploy | L1/L2 node deployment (Docker Compose, OpenWebUI + llama.cpp) |
| rare-archive-compliance | aDNA schemas, FAIR scoring, governance, CI validation |
