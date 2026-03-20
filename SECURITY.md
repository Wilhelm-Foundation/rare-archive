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
