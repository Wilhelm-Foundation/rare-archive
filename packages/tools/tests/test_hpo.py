"""Tests for HPO adapter."""

import httpx
import respx

from rare_archive_tools.adapters.hpo import HPOAdapter

BASE = "https://ontology.jax.org/api/hp"


class TestHPO:
    @respx.mock
    def test_search_term(self, hpo_search_response):
        respx.get(f"{BASE}/search").mock(
            return_value=httpx.Response(200, json=hpo_search_response)
        )
        adapter = HPOAdapter()
        result = adapter.search_term("seizure")
        assert "terms" in result

    @respx.mock
    def test_get_term(self, hpo_term_response):
        respx.get(f"{BASE}/terms/HP:0001250").mock(
            return_value=httpx.Response(200, json=hpo_term_response)
        )
        adapter = HPOAdapter()
        result = adapter.get_term("HP:0001250")
        assert result["id"] == "HP:0001250"

    @respx.mock
    def test_lookup_found(self, hpo_search_response):
        respx.get(f"{BASE}/search").mock(
            return_value=httpx.Response(200, json=hpo_search_response)
        )
        adapter = HPOAdapter()
        result = adapter.lookup("seizure")
        assert result["found"] is True
        assert result["total_results"] == 2

    @respx.mock
    def test_lookup_not_found(self):
        respx.get(f"{BASE}/search").mock(
            return_value=httpx.Response(200, json={"terms": []})
        )
        adapter = HPOAdapter()
        result = adapter.lookup("nonexistent_phenotype_xyz")
        assert result["found"] is False
