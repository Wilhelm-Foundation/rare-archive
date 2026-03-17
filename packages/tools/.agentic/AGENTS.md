# Rare Archive Tool Harness — Agentic DNA

## Purpose
Clinical tool-use harness: 7 diagnostic tool integrations, OpenWebUI tool definitions, MCP server wrappers.

## Tools
| Tool | API Source | Function |
|------|-----------|----------|
| ClinVar | NCBI E-Utils | Variant pathogenicity lookup |
| Orphanet | Orphadata API | Rare disease information |
| PanelApp | Genomics England | Gene panel queries |
| gnomAD | gnomAD API | Population allele frequencies |
| HPO | HPO API | Phenotype term resolution |
| PubMed | NCBI E-Utils | Literature search |
| Differential Dx | Composite | Ranked differential diagnosis |

## Key Directories
- `src/rare_archive_tools/adapters/`: Base adapter interface, rate limiting, Redis caching
- `src/rare_archive_tools/openwebui/`: OpenWebUI tool definition files
- `src/rare_archive_tools/mcp/`: MCP server wrappers for tool-use outside OpenWebUI
- `prompts/`: Category-specific system prompts for clinical reasoning
