"""Tests for PubMed adapter."""

import httpx
import respx

from rare_archive_tools.adapters.pubmed import PubMedAdapter

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class TestPubMed:
    @respx.mock
    def test_search(self, esearch_response):
        respx.get(f"{BASE}/esearch.fcgi").mock(
            return_value=httpx.Response(200, json=esearch_response)
        )
        adapter = PubMedAdapter()
        result = adapter.search("Marfan syndrome")
        assert result["esearchresult"]["idlist"] == ["12345"]

    @respx.mock
    def test_fetch_abstracts(self, efetch_response):
        respx.get(f"{BASE}/efetch.fcgi").mock(
            return_value=httpx.Response(200, json=efetch_response)
        )
        adapter = PubMedAdapter()
        result = adapter.fetch_abstracts(["12345"])
        assert "result" in result

    @respx.mock
    def test_lookup_found(self, esearch_response):
        respx.get(f"{BASE}/esearch.fcgi").mock(
            return_value=httpx.Response(200, json=esearch_response)
        )
        adapter = PubMedAdapter()
        result = adapter.lookup("Marfan syndrome")
        assert result["found"] is True
        assert "12345" in result["pmids"]

    @respx.mock
    def test_lookup_not_found(self, esearch_empty_response):
        respx.get(f"{BASE}/esearch.fcgi").mock(
            return_value=httpx.Response(200, json=esearch_empty_response)
        )
        adapter = PubMedAdapter()
        result = adapter.lookup("nonexistent_query_xyz")
        assert result["found"] is False
