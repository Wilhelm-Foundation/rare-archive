"""Tests for ClinVar adapter."""

import httpx
import respx

from rare_archive_tools.adapters.clinvar import ClinVarAdapter

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class TestClinVar:
    @respx.mock
    def test_search_variant(self, esearch_response):
        respx.get(f"{BASE}/esearch.fcgi").mock(
            return_value=httpx.Response(200, json=esearch_response)
        )
        adapter = ClinVarAdapter()
        result = adapter.search_variant("NM_000546.6:c.215C>G", gene="TP53")
        assert result["esearchresult"]["idlist"] == ["12345"]

    @respx.mock
    def test_fetch_variant(self, efetch_response):
        respx.get(f"{BASE}/efetch.fcgi").mock(
            return_value=httpx.Response(200, json=efetch_response)
        )
        adapter = ClinVarAdapter()
        result = adapter.fetch_variant("12345")
        assert "result" in result

    @respx.mock
    def test_lookup_found(self, esearch_response, efetch_response):
        respx.get(f"{BASE}/esearch.fcgi").mock(
            return_value=httpx.Response(200, json=esearch_response)
        )
        respx.get(f"{BASE}/efetch.fcgi").mock(
            return_value=httpx.Response(200, json=efetch_response)
        )
        adapter = ClinVarAdapter()
        result = adapter.lookup("NM_000546.6:c.215C>G")
        assert result["found"] is True
        assert result["variant_id"] == "12345"

    @respx.mock
    def test_lookup_not_found(self, esearch_empty_response):
        respx.get(f"{BASE}/esearch.fcgi").mock(
            return_value=httpx.Response(200, json=esearch_empty_response)
        )
        adapter = ClinVarAdapter()
        result = adapter.lookup("NONEXISTENT")
        assert result["found"] is False

    @respx.mock
    def test_search_variant_gene_filter(self, esearch_response):
        route = respx.get(f"{BASE}/esearch.fcgi").mock(
            return_value=httpx.Response(200, json=esearch_response)
        )
        adapter = ClinVarAdapter()
        adapter.search_variant("rs28934578", gene="TP53")
        request = route.calls[0].request
        assert b"TP53" in request.url.params.get("term", "").encode()
