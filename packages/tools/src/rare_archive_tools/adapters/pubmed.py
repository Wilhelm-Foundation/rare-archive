"""PubMed adapter — NCBI literature search."""

from typing import Any

from .base import AdapterConfig, BaseAdapter


class PubMedAdapter(BaseAdapter):
    """Adapter for NCBI PubMed via E-Utilities."""

    def __init__(self, api_key: str = "", email: str = ""):
        config = AdapterConfig(
            base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
            auth_type="api_key" if api_key else "none",
            api_key=api_key,
        )
        super().__init__(config)
        self._email = email

    def tool_name(self) -> str:
        return "pubmed_literature_search"

    def tool_description(self) -> str:
        return "Search PubMed for relevant medical literature on rare diseases"

    def search(self, query: str, max_results: int = 5) -> dict[str, Any]:
        """Search PubMed."""
        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": max_results,
            "sort": "relevance",
        }
        if self._email:
            params["email"] = self._email
        return self._request("GET", "esearch.fcgi", params=params)

    def fetch_abstracts(self, pmids: list[str]) -> dict[str, Any]:
        """Fetch article details."""
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "json",
            "rettype": "abstract",
        }
        return self._request("GET", "efetch.fcgi", params=params)

    def lookup(self, query: str, max_results: int = 5) -> dict[str, Any]:
        """Search and fetch abstracts."""
        search = self.search(query, max_results)
        ids = search.get("esearchresult", {}).get("idlist", [])

        if not ids:
            return {"found": False, "query": query}

        return {
            "found": True,
            "query": query,
            "total_results": int(search.get("esearchresult", {}).get("count", 0)),
            "pmids": ids,
        }
