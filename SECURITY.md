# Security Policy

## Reporting a Vulnerability

The Rare AI Archive processes clinical decision-support scenarios. While we use only synthetic patient data (never real PHI), we take security seriously.

**To report a security vulnerability:**

1. **Do NOT open a public GitHub issue.**
2. Email **security@wilhelm.foundation** with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
3. You will receive an acknowledgment within 48 hours.
4. We aim to provide a fix or mitigation within 7 days for critical issues.

## Scope

| In Scope | Out of Scope |
|----------|-------------|
| Authentication/authorization flaws | Social engineering |
| Data leakage (synthetic or configuration) | Denial of service |
| Dependency vulnerabilities | Issues in upstream dependencies (report to them directly) |
| Docker container escapes | Physical security |
| API injection or abuse | |

## Supported Versions

| Version | Supported |
|---------|-----------|
| main branch | Yes |
| Tagged releases | Yes |
| Feature branches | No |

## Data Handling

- **No real patient data** is stored, processed, or transmitted by this system.
- All training data uses synthetic patients generated from published medical literature.
- Clinical tool adapters query public APIs (ClinVar, Orphanet, etc.) — no PHI is sent.
- See our [CONTRIBUTING.md](CONTRIBUTING.md) for the PHI-free commitment.

## Federated Deployment Security

The Archive is designed for multi-site deployment where training data never leaves the originating institution:

- **Node-to-node authentication**: Tailscale mesh networking with TLS for all inter-node communication
- **Data sovereignty**: Model weights and GGUF artifacts can be distributed; raw training data stays local
- **Access control**: JupyterHub SSO with per-user role assignments for Arena evaluators and operators
- **Container isolation**: All services run in Docker containers on an isolated bridge network with NGINX reverse proxy

## Arena Data Governance

The ELO Arena produces evaluation data (preference pairs, corrections, ELO ratings) that feeds back into model training:

- **No PHI in evaluations**: All Arena cases use synthetic vignettes — clinician evaluations contain clinical reasoning, not patient data
- **Correction audit trail**: Every correction is logged with expert ID, timestamp, and case reference in PostgreSQL
- **Preference export transparency**: HuggingFace exports use evaluation_id-based deduplication and are publicly auditable
- **Role-based access**: Correction submission requires registered expert status; export operations require operator credentials
