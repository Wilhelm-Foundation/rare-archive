"""Orphanet adapter — Rare disease information lookup.

API: Orphadata REST API
"""

from typing import Any

from .base import AdapterConfig, BaseAdapter


class OrphanetAdapter(BaseAdapter):
    """Adapter for Orphanet/Orphadata API."""

    def __init__(self):
        config = AdapterConfig(
            base_url="https://api.orphadata.com/rd-api/",
        )
        super().__init__(config)

    def tool_name(self) -> str:
        return "orphanet_disease_search"

    def tool_description(self) -> str:
        return "Search Orphanet for rare disease information, prevalence, and associated genes"

    def search_disease(self, query: str, lang: str = "en") -> dict[str, Any]:
        """Search for a disease by name or synonym."""
        params = {"query": query, "lang": lang}
        return self._request("GET", "diseases/search", params=params)

    def get_disease(self, orpha_code: str) -> dict[str, Any]:
        """Get detailed disease information by Orphanet code."""
        return self._request("GET", f"diseases/{orpha_code}")

    def get_disease_genes(self, orpha_code: str) -> dict[str, Any]:
        """Get genes associated with a disease."""
        return self._request("GET", f"diseases/{orpha_code}/genes")

    def get_disease_phenotypes(self, orpha_code: str) -> dict[str, Any]:
        """Get HPO phenotypes associated with a disease."""
        return self._request("GET", f"diseases/{orpha_code}/phenotypes")

    def lookup(self, disease_name: str) -> dict[str, Any]:
        """Combined search and detail fetch."""
        results = self.search_disease(disease_name)
        diseases = results.get("results", [])

        if not diseases:
            return {"found": False, "query": disease_name, "message": "No diseases found"}

        top = diseases[0]
        orpha_code = top.get("orphaCode", top.get("id", ""))
        detail = self.get_disease(str(orpha_code)) if orpha_code else {}

        return {
            "found": True,
            "query": disease_name,
            "orpha_code": orpha_code,
            "total_results": len(diseases),
            "top_result": top,
            "details": detail,
        }
