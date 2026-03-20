"""Tests for gnomAD adapter."""

import httpx
import respx

from rare_archive_tools.adapters.gnomad import GnomADAdapter

BASE = "https://gnomad.broadinstitute.org/api"


class TestGnomAD:
    @respx.mock
    def test_query_variant(self, gnomad_variant_response):
        respx.post(f"{BASE}/").mock(
            return_value=httpx.Response(200, json=gnomad_variant_response)
        )
        adapter = GnomADAdapter()
        result = adapter.query_variant("1-55505647-C-T")
        assert result["data"]["variant"]["variant_id"] == "1-55505647-C-T"

    @respx.mock
    def test_lookup_found(self, gnomad_variant_response):
        respx.post(f"{BASE}/").mock(
            return_value=httpx.Response(200, json=gnomad_variant_response)
        )
        adapter = GnomADAdapter()
        result = adapter.lookup("1-55505647-C-T")
        assert result["found"] is True
        assert result["genome_af"] == 0.0001
        assert result["exome_af"] == 0.0001

    @respx.mock
    def test_lookup_not_found(self, gnomad_empty_response):
        respx.post(f"{BASE}/").mock(
            return_value=httpx.Response(200, json=gnomad_empty_response)
        )
        adapter = GnomADAdapter()
        result = adapter.lookup("99-999999-A-G")
        assert result["found"] is False
