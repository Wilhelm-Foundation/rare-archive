"""ClinVar adapter — NCBI variant pathogenicity lookup.

API: NCBI E-Utilities (E-Search + E-Fetch)
Rate limit: 3 req/s without API key, 10 req/s with API key
"""

from typing import Any

from .base import AdapterConfig, BaseAdapter


class ClinVarAdapter(BaseAdapter):
    """Adapter for NCBI ClinVar via E-Utilities."""

    def __init__(self, api_key: str = "", email: str = ""):
        config = AdapterConfig(
            base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
            auth_type="api_key" if api_key else "none",
            api_key=api_key,
        )
        super().__init__(config)
        self._email = email

    def tool_name(self) -> str:
        return "clinvar_variant_lookup"

    def tool_description(self) -> str:
        return "Look up variant pathogenicity classifications in NCBI ClinVar"

    def search_variant(self, variant: str, gene: str | None = None) -> dict[str, Any]:
        """Search ClinVar for a variant.

        Args:
            variant: Variant description (e.g., "NM_000546.6:c.215C>G" or "rs28934578")
            gene: Optional gene symbol to narrow search

        Returns:
            Dict with variant IDs and summary info
        """
        query = variant
        if gene:
            query = f"{variant} AND {gene}[gene]"

        params = {
            "db": "clinvar",
            "term": query,
            "retmode": "json",
            "retmax": 10,
        }
        if self._email:
            params["email"] = self._email

        result = self._request("GET", "esearch.fcgi", params=params)
        return result

    def fetch_variant(self, variant_id: str) -> dict[str, Any]:
        """Fetch detailed ClinVar variant record.

        Args:
            variant_id: ClinVar variation ID

        Returns:
            Detailed variant record with pathogenicity, conditions, etc.
        """
        params = {
            "db": "clinvar",
            "id": variant_id,
            "rettype": "vcv",
            "retmode": "json",
        }
        return self._request("GET", "efetch.fcgi", params=params)

    def lookup(self, variant: str, gene: str | None = None) -> dict[str, Any]:
        """Combined search and fetch for a variant.

        Returns structured result with pathogenicity classification.
        """
        search = self.search_variant(variant, gene)
        ids = search.get("esearchresult", {}).get("idlist", [])

        if not ids:
            return {
                "found": False,
                "query": variant,
                "message": "No ClinVar entries found",
            }

        details = self.fetch_variant(ids[0])
        return {
            "found": True,
            "query": variant,
            "variant_id": ids[0],
            "total_results": int(search.get("esearchresult", {}).get("count", 0)),
            "details": details,
        }
