# Rare Archive RLHF — Agentic DNA

## Purpose
RLHF portal backend extending OpenWebUI Arena mode with multi-dimensional ELO tracking, expert matching, and preference data export.

## Key Components
- `src/archive_api/`: FastAPI sidecar for ELO tracking and preference capture
- `src/archive_api/elo/`: Multi-dimensional ELO per (model_id, patient_category, evaluation_mode)
- `src/archive_api/export/`: Nightly preference pair export to HuggingFace for DPO/GRPO
- `frontend/`: OpenWebUI custom annotation tool (structured feedback form)

## Evaluation Flow
1. Expert registers via JupyterHub SSO → subspecialty profile
2. System matches expert to patient-category-appropriate synthetic cases
3. Arena mode: two anonymized models respond to same clinical vignette
4. Expert selects preferred + structured annotation (accuracy, reasoning, tool use, safety — 0-5 each)
5. Multi-dimensional ELO updated
6. Preference pairs exported nightly to HF dataset
