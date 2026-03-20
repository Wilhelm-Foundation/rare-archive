"""Tests for PanelApp adapter."""

import httpx
import respx

from rare_archive_tools.adapters.panelapp import PanelAppAdapter

BASE = "https://panelapp.genomicsengland.co.uk/api/v1"


class TestPanelApp:
    @respx.mock
    def test_search_panels(self, panelapp_search_response):
        respx.get(f"{BASE}/panels/").mock(
            return_value=httpx.Response(200, json=panelapp_search_response)
        )
        adapter = PanelAppAdapter()
        result = adapter.search_panels("intellectual disability")
        assert result["count"] == 1

    @respx.mock
    def test_get_panel(self, panelapp_panel_response):
        respx.get(f"{BASE}/panels/1/").mock(
            return_value=httpx.Response(200, json=panelapp_panel_response)
        )
        adapter = PanelAppAdapter()
        result = adapter.get_panel("1")
        assert result["name"] == "Intellectual disability"

    @respx.mock
    def test_search_genes(self, panelapp_genes_response):
        respx.get(f"{BASE}/genes/").mock(
            return_value=httpx.Response(200, json=panelapp_genes_response)
        )
        adapter = PanelAppAdapter()
        result = adapter.search_genes("MECP2")
        assert result["count"] == 1

    @respx.mock
    def test_lookup_found(self, panelapp_search_response):
        respx.get(f"{BASE}/panels/").mock(
            return_value=httpx.Response(200, json=panelapp_search_response)
        )
        adapter = PanelAppAdapter()
        result = adapter.lookup("intellectual disability")
        assert result["found"] is True
        assert result["total_results"] == 1

    @respx.mock
    def test_lookup_not_found(self):
        respx.get(f"{BASE}/panels/").mock(
            return_value=httpx.Response(200, json={"count": 0, "results": []})
        )
        adapter = PanelAppAdapter()
        result = adapter.lookup("nonexistent_panel_xyz")
        assert result["found"] is False
