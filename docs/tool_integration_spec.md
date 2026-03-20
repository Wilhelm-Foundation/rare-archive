# Tool Integration Spec — Rare AI Archive

How to add new clinical tools to the Rare AI Archive.

## Architecture

```
External API ──▶ Adapter (Python) ──▶ OpenWebUI Tool (pipeline)
                     │
                     ├── Rate limiting
                     ├── Response caching
                     ├── Error handling
                     └── Structured output
```

Each tool has two components:
1. **Adapter** (`packages/tools/src/rare_archive_tools/adapters/`) — reusable Python class that wraps the external API
2. **OpenWebUI tool** (`packages/tools/src/rare_archive_tools/openwebui/`) — thin wrapper that bridges the adapter to OpenWebUI's tool interface

## Adapter Interface

All adapters follow this pattern:

```python
from rare_archive_tools.adapters.base import BaseAdapter

class NewToolAdapter(BaseAdapter):
    """Adapter for [External Service Name]."""

    BASE_URL = "https://api.example.org"
    RATE_LIMIT = 2.0  # requests per second
    CACHE_TTL = 3600  # seconds (1 hour default)

    def __init__(self, api_key: str | None = None):
        super().__init__(api_key=api_key)

    def lookup(self, query: str) -> dict:
        """Primary lookup method. Returns structured result."""
        url = f"{self.BASE_URL}/search"
        params = {"q": query, "format": "json"}
        response = self._get(url, params=params)
        return self._parse_response(response)

    def _parse_response(self, response: dict) -> dict:
        """Parse API response into standardized format."""
        return {
            "source": "new_tool",
            "query": response.get("query"),
            "results": [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "relevance": r.get("score", 0),
                }
                for r in response.get("results", [])
            ],
            "metadata": {
                "api_version": response.get("version"),
                "result_count": len(response.get("results", [])),
            },
        }
```

### BaseAdapter Provides

- `_get(url, params)` — HTTP GET with rate limiting, retries, and caching
- `_post(url, data)` — HTTP POST with same protections
- Automatic response caching (configurable TTL)
- Rate limiting via token bucket
- Structured error handling (returns error dict, never raises to caller)

## OpenWebUI Tool Wrapper

```python
class Tools:
    class Valves(BaseModel):
        api_key: str = Field(default="", description="API key (optional)")

    def __init__(self):
        self.valves = self.Valves()

    async def lookup_new_tool(self, query: str) -> str:
        """Look up [description] for a given query.

        :param query: The search term (gene name, disease, variant, etc.)
        :return: Formatted results from [External Service]
        """
        from rare_archive_tools.adapters.new_tool import NewToolAdapter

        adapter = NewToolAdapter(api_key=self.valves.api_key)
        result = adapter.lookup(query)

        if "error" in result:
            return f"Error querying [service]: {result['error']}"

        lines = [f"## [Service] Results for: {query}", ""]
        for r in result["results"]:
            lines.append(f"- **{r['name']}** (ID: {r['id']})")

        return "\n".join(lines)
```

## Adding a New Tool — Checklist

1. **Create adapter** in `packages/tools/src/rare_archive_tools/adapters/new_tool.py`
   - Implement `lookup()` method
   - Set `BASE_URL`, `RATE_LIMIT`, `CACHE_TTL`
   - Handle API-specific error codes

2. **Create OpenWebUI tool** in `packages/tools/src/rare_archive_tools/openwebui/new_tool.py`
   - Wrap adapter call
   - Format output as Markdown for chat display
   - Add Valves for configurable parameters

3. **Write tests** in `packages/tools/tests/test_new_tool.py`
   - Mock external API with `respx`
   - Test happy path, error cases, rate limiting
   - Test with realistic response fixtures

4. **Register in ontology** — add entry to `packages/ontology/schemas/clinical_tool.json`

5. **Update this table** in `packages/tools/README.md`

6. **Deploy** — copy OpenWebUI tool file to the running instance

## Rate Limiting Reference

| API | Limit | Auth Required | Notes |
|-----|-------|---------------|-------|
| NCBI E-Utils | 3/sec (10 with key) | Optional (API key) | ClinVar, PubMed |
| Orphadata | ~1/sec | No | Restructured 2026-03 |
| HPO JAX | ~2/sec | No | Some endpoints removed 2026-03 |
| PanelApp | ~2/sec | No | UK Genomics England |
| gnomAD GraphQL | ~5/sec | No | Schema changes possible |

## Error Handling

Adapters return error dicts rather than raising exceptions:

```python
# Error response format
{
    "error": "API returned 404",
    "source": "orphanet",
    "query": "ORPHA:1234",
    "status_code": 404
}
```

The OpenWebUI wrapper converts these to user-friendly messages. The model sees the error text and can adjust its reasoning (e.g., suggest alternative lookup strategies).

## Caching Strategy

- Default TTL: 1 hour (3600s)
- Cache key: `(adapter_name, method, query_params)`
- Storage: in-memory dict (per-process). Redis optional via `pip install -e ".[redis]"`
- Cache is not shared between OpenWebUI tool instances (each worker has its own)

Increase TTL for stable data (Orphanet disease definitions: 24h). Decrease for volatile data (gnomAD population frequencies during schema transitions: 15min).
