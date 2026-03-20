"""Orphanet adapter — Rare disease information lookup.

API: Orphadata REST API (restructured 2025 — domain-based endpoints)
"""

from typing import Any

import httpx

from .base import AdapterConfig, BaseAdapter


class OrphanetAdapter(BaseAdapter):
    """Adapter for Orphanet/Orphadata API.

    Endpoints are domain-based:
      /rd-cross-referencing/orphacodes/names/{name}  — disease lookup by name
      /rd-associated-genes/orphacodes/{orphacode}     — genes for a disease
      /rd-phenotypes/orphacodes/{orphacode}            — HPO phenotypes
      /rd-epidemiology/orphacodes/{orphacode}          — prevalence data
    """

    def __init__(self):
        config = AdapterConfig(
            base_url="https://api.orphadata.com/",
        )
        super().__init__(config)

    def tool_name(self) -> str:
        return "orphanet_disease_search"

    def tool_description(self) -> str:
        return "Search Orphanet for rare disease information, prevalence, and associated genes"

    def search_disease(self, query: str) -> dict[str, Any]:
        """Search for a disease by name."""
        return self._request("GET", f"rd-cross-referencing/orphacodes/names/{query}")

    def get_disease(self, orpha_code: str) -> dict[str, Any]:
        """Get cross-referencing data for a disease by Orphanet code."""
        return self._request("GET", f"rd-cross-referencing/orphacodes/{orpha_code}")

    def get_disease_genes(self, orpha_code: str) -> dict[str, Any]:
        """Get genes associated with a disease."""
        return self._request("GET", f"rd-associated-genes/orphacodes/{orpha_code}")

    def get_disease_phenotypes(self, orpha_code: str) -> dict[str, Any]:
        """Get HPO phenotypes associated with a disease."""
        return self._request("GET", f"rd-phenotypes/orphacodes/{orpha_code}")

    def lookup(self, disease_name: str) -> dict[str, Any]:
        """Search by name and return structured result."""
        try:
            result = self.search_disease(disease_name)
        except (httpx.HTTPStatusError, RuntimeError):
            return {"found": False, "query": disease_name, "message": "No diseases found"}

        data = result.get("data", {})

        if not data or data.get("__count", 0) == 0:
            return {"found": False, "query": disease_name, "message": "No diseases found"}

        results = data.get("results", data)
        name = results.get("Preferred term", disease_name)
        orpha_code = results.get("ORPHAcode", "")
        disorder_group = results.get("DisorderGroup", "")

        return {
            "found": True,
            "query": disease_name,
            "name": name,
            "orpha_code": orpha_code,
            "disorder_group": disorder_group,
            "details": results,
        }
