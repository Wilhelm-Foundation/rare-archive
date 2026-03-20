"""Tests for Orphanet adapter."""

import httpx
import respx

from rare_archive_tools.adapters.orphanet import OrphanetAdapter

BASE = "https://api.orphadata.com"


class TestOrphanet:
    @respx.mock
    def test_search_disease(self, orphanet_search_response):
        respx.get(f"{BASE}/rd-cross-referencing/orphacodes/names/Marfan").mock(
            return_value=httpx.Response(200, json=orphanet_search_response)
        )
        adapter = OrphanetAdapter()
        result = adapter.search_disease("Marfan")
        assert "data" in result
        assert result["data"]["__count"] == 1
        assert result["data"]["results"]["ORPHAcode"] == 558

    @respx.mock
    def test_get_disease(self, orphanet_disease_response):
        respx.get(f"{BASE}/rd-cross-referencing/orphacodes/558").mock(
            return_value=httpx.Response(200, json=orphanet_disease_response)
        )
        adapter = OrphanetAdapter()
        result = adapter.get_disease("558")
        assert result["data"]["results"]["ORPHAcode"] == 558

    @respx.mock
    def test_get_disease_genes(self, orphanet_genes_response):
        respx.get(f"{BASE}/rd-associated-genes/orphacodes/558").mock(
            return_value=httpx.Response(200, json=orphanet_genes_response)
        )
        adapter = OrphanetAdapter()
        result = adapter.get_disease_genes("558")
        genes = result["data"]["results"]["DisorderGeneAssociation"]
        assert genes[0]["Gene"]["Symbol"] == "FBN1"

    @respx.mock
    def test_lookup_found(self, orphanet_search_response):
        respx.get(f"{BASE}/rd-cross-referencing/orphacodes/names/Marfan%20syndrome").mock(
            return_value=httpx.Response(200, json=orphanet_search_response)
        )
        adapter = OrphanetAdapter()
        result = adapter.lookup("Marfan syndrome")
        assert result["found"] is True
        assert result["orpha_code"] == 558

    @respx.mock
    def test_lookup_not_found(self):
        respx.get(f"{BASE}/rd-cross-referencing/orphacodes/names/nonexistent_disease_xyz").mock(
            return_value=httpx.Response(
                404,
                json={"error": {"code": 404, "message": "message to define", "type": "Query not found"}},
            )
        )
        adapter = OrphanetAdapter()
        result = adapter.lookup("nonexistent_disease_xyz")
        assert result["found"] is False
