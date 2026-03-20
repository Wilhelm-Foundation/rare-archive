# Rare Archive Tool Harness

Clinical diagnostic tool integrations for the [Rare AI Archive](https://github.com/wilhelm-foundation/rare-ai-archive).

## Tools

| Tool | Source | OpenWebUI | MCP |
|------|--------|-----------|------|
| ClinVar | NCBI E-Utils | clinvar_tool.py | — |
| Orphanet | Orphadata API | orphanet_tool.py | — |
| HPO | HPO JAX API | hpo_tool.py | — |
| PanelApp | Genomics England | panelapp_tool.py | — |
| gnomAD | gnomAD GraphQL | gnomad_tool.py | — |
| PubMed | NCBI E-Utils | pubmed_tool.py | — |
| Differential Dx | Composite | differential_dx_tool.py | — |

## Installation

```bash
pip install -e .

# With Redis caching:
pip install -e ".[redis]"
```

## Usage

### Python Adapters
```python
from rare_archive_tools.adapters.clinvar import ClinVarAdapter

clinvar = ClinVarAdapter(api_key="your_key")
result = clinvar.lookup("BRCA1 c.5266dupC")
```

### OpenWebUI
Copy tool files from `src/rare_archive_tools/openwebui/` into OpenWebUI's tool directory.

> **Note**: MCP tool server integration is deferred. All 7 tools are currently served as OpenWebUI native tools. MCP would require a separate server process and is tracked for future federation work.

## License

Apache 2.0
