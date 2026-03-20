"""Tests for Orphanet adapter."""

import httpx
import respx

from rare_archive_tools.adapters.orphanet import OrphanetAdapter

BASE = "https://api.orphadata.com/rd-api"


class TestOrphanet:
    @respx.mock
    def test_search_disease(self, orphanet_search_response):
        respx.get(f"{BASE}/diseases/search").mock(
            return_value=httpx.Response(200, json=orphanet_search_response)
        )
        adapter = OrphanetAdapter()
        result = adapter.search_disease("Marfan")
        assert "results" in result

    @respx.mock
    def test_get_disease(self, orphanet_disease_response):
        respx.get(f"{BASE}/diseases/558").mock(
            return_value=httpx.Response(200, json=orphanet_disease_response)
        )
        adapter = OrphanetAdapter()
        result = adapter.get_disease("558")
        assert result["orphaCode"] == 558

    @respx.mock
    def test_get_disease_genes(self, orphanet_genes_response):
        respx.get(f"{BASE}/diseases/558/genes").mock(
            return_value=httpx.Response(200, json=orphanet_genes_response)
        )
        adapter = OrphanetAdapter()
        result = adapter.get_disease_genes("558")
        assert result["genes"][0]["symbol"] == "FBN1"

    @respx.mock
    def test_lookup_found(self, orphanet_search_response, orphanet_disease_response):
        respx.get(f"{BASE}/diseases/search").mock(
            return_value=httpx.Response(200, json=orphanet_search_response)
        )
        respx.get(f"{BASE}/diseases/558").mock(
            return_value=httpx.Response(200, json=orphanet_disease_response)
        )
        adapter = OrphanetAdapter()
        result = adapter.lookup("Marfan syndrome")
        assert result["found"] is True
        assert result["orpha_code"] == 558

    @respx.mock
    def test_lookup_not_found(self):
        respx.get(f"{BASE}/diseases/search").mock(
            return_value=httpx.Response(200, json={"results": []})
        )
        adapter = OrphanetAdapter()
        result = adapter.lookup("nonexistent_disease_xyz")
        assert result["found"] is False
