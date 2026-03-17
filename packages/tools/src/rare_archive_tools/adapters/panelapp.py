"""PanelApp adapter — Genomics England gene panel queries."""

from typing import Any

from .base import AdapterConfig, BaseAdapter


class PanelAppAdapter(BaseAdapter):
    """Adapter for Genomics England PanelApp API."""

    def __init__(self):
        config = AdapterConfig(
            base_url="https://panelapp.genomicsengland.co.uk/api/v1/",
        )
        super().__init__(config)

    def tool_name(self) -> str:
        return "panelapp_gene_panel"

    def tool_description(self) -> str:
        return "Query Genomics England PanelApp for curated gene panels by disease or gene"

    def search_panels(self, query: str) -> dict[str, Any]:
        """Search for gene panels by name or disease."""
        params = {"search": query}
        return self._request("GET", "panels/", params=params)

    def get_panel(self, panel_id: str, version: str | None = None) -> dict[str, Any]:
        """Get a specific gene panel with its genes."""
        endpoint = f"panels/{panel_id}/"
        params = {}
        if version:
            params["version"] = version
        return self._request("GET", endpoint, params=params)

    def search_genes(self, gene_symbol: str) -> dict[str, Any]:
        """Search for a gene across all panels."""
        params = {"search": gene_symbol}
        return self._request("GET", "genes/", params=params)

    def lookup(self, query: str) -> dict[str, Any]:
        """Search panels and return structured results."""
        results = self.search_panels(query)
        panels = results.get("results", [])

        return {
            "found": bool(panels),
            "query": query,
            "total_results": results.get("count", len(panels)),
            "panels": [
                {
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "disease_group": p.get("disease_group"),
                    "gene_count": p.get("stats", {}).get("number_of_genes", 0),
                    "version": p.get("version"),
                }
                for p in panels[:10]
            ],
        }
