"""HPO adapter — Human Phenotype Ontology term resolution.

API: HPO JAX API
"""

from typing import Any

from .base import AdapterConfig, BaseAdapter


class HPOAdapter(BaseAdapter):
    """Adapter for the Human Phenotype Ontology API."""

    def __init__(self):
        config = AdapterConfig(
            base_url="https://ontology.jax.org/api/hp/",
        )
        super().__init__(config)

    def tool_name(self) -> str:
        return "hpo_term_lookup"

    def tool_description(self) -> str:
        return "Resolve clinical phenotypes to HPO terms and explore phenotype relationships"

    def search_term(self, query: str, max_results: int = 10) -> dict[str, Any]:
        """Search for HPO terms matching a clinical description."""
        params = {"q": query, "max": max_results}
        return self._request("GET", "search", params=params)

    def get_term(self, hpo_id: str) -> dict[str, Any]:
        """Get details for a specific HPO term."""
        return self._request("GET", f"terms/{hpo_id}")

    def get_term_diseases(self, hpo_id: str) -> dict[str, Any]:
        """Get diseases associated with an HPO term."""
        return self._request("GET", f"terms/{hpo_id}/diseases")

    def get_term_genes(self, hpo_id: str) -> dict[str, Any]:
        """Get genes associated with an HPO term."""
        return self._request("GET", f"terms/{hpo_id}/genes")

    def lookup(self, phenotype_description: str) -> dict[str, Any]:
        """Search for a phenotype and return enriched results."""
        results = self.search_term(phenotype_description)
        terms = results.get("terms", results.get("results", []))

        if not terms:
            return {"found": False, "query": phenotype_description}

        return {
            "found": True,
            "query": phenotype_description,
            "total_results": len(terms),
            "terms": terms[:5],
        }
