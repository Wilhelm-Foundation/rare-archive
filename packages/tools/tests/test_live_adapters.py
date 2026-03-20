"""Live adapter tests — hit real external APIs.

All tests in this module are marked ``@pytest.mark.live`` and are skipped by
default (see root ``pyproject.toml`` ``addopts``).  Run explicitly with::

    pytest packages/tools/tests/test_live_adapters.py -m live -v --timeout=30
"""

import asyncio
import functools
import json
import time

import httpx
import pytest

from rare_archive_tools.adapters.clinvar import ClinVarAdapter
from rare_archive_tools.adapters.gnomad import GnomADAdapter
from rare_archive_tools.adapters.hpo import HPOAdapter
from rare_archive_tools.adapters.orphanet import OrphanetAdapter
from rare_archive_tools.adapters.panelapp import PanelAppAdapter
from rare_archive_tools.adapters.pubmed import PubMedAdapter
from rare_archive_tools.openwebui.differential_dx_tool import Tools as DiffDxTools


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _skip_on_network_error(fn):
    """Decorator: ``pytest.skip()`` on network or transient API errors."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as exc:
            pytest.skip(f"Network unavailable: {exc}")
        except json.JSONDecodeError as exc:
            pytest.skip(f"API returned non-JSON response: {exc}")

    return wrapper


@pytest.fixture(autouse=True)
def _rate_limit_pause():
    """Pause between live API calls to be a good citizen."""
    yield
    time.sleep(0.5)


# ---------------------------------------------------------------------------
# ClinVar
# ---------------------------------------------------------------------------

@pytest.mark.live
class TestClinVarLive:
    def setup_method(self):
        self.adapter = ClinVarAdapter()

    def teardown_method(self):
        self.adapter.close()

    @_skip_on_network_error
    def test_search_variant(self):
        result = self.adapter.search_variant("c.1226A>G", gene="GBA1")
        id_list = result.get("esearchresult", {}).get("idlist", [])
        assert isinstance(id_list, list)
        assert len(id_list) > 0, "Expected at least one ClinVar hit for GBA1 c.1226A>G"

    @_skip_on_network_error
    def test_lookup(self):
        result = self.adapter.lookup("c.1226A>G", gene="GBA1")
        assert result["found"] is True
        assert "variant_id" in result


# ---------------------------------------------------------------------------
# Orphanet
# ---------------------------------------------------------------------------

@pytest.mark.live
class TestOrphanetLive:
    def setup_method(self):
        self.adapter = OrphanetAdapter()

    def teardown_method(self):
        self.adapter.close()

    @_skip_on_network_error
    def test_search_disease(self):
        result = self.adapter.search_disease("Gaucher disease")
        orpha_code = result.get("data", {}).get("results", {}).get("ORPHAcode")
        assert isinstance(orpha_code, int), "Expected integer ORPHAcode"

    @_skip_on_network_error
    def test_lookup(self):
        result = self.adapter.lookup("Gaucher disease")
        assert result["found"] is True
        assert "orpha_code" in result


# ---------------------------------------------------------------------------
# HPO
# ---------------------------------------------------------------------------

@pytest.mark.live
class TestHPOLive:
    def setup_method(self):
        self.adapter = HPOAdapter()

    def teardown_method(self):
        self.adapter.close()

    @_skip_on_network_error
    def test_search_term(self):
        result = self.adapter.search_term("hepatosplenomegaly")
        terms = result.get("terms", result.get("results", []))
        assert isinstance(terms, list)
        assert len(terms) > 0, "Expected at least one HPO term for hepatosplenomegaly"

    @_skip_on_network_error
    def test_lookup(self):
        result = self.adapter.lookup("hepatosplenomegaly")
        assert result["found"] is True
        assert result["total_results"] > 0


# ---------------------------------------------------------------------------
# PanelApp
# ---------------------------------------------------------------------------

@pytest.mark.live
class TestPanelAppLive:
    def setup_method(self):
        self.adapter = PanelAppAdapter()

    def teardown_method(self):
        self.adapter.close()

    @_skip_on_network_error
    def test_search_panels(self):
        result = self.adapter.search_panels("muscular dystrophy")
        results = result.get("results", [])
        assert isinstance(results, list)
        assert len(results) > 0, "Expected at least one panel for muscular dystrophy"

    @_skip_on_network_error
    def test_lookup(self):
        result = self.adapter.lookup("muscular dystrophy")
        assert result["found"] is True
        assert result["total_results"] > 0


# ---------------------------------------------------------------------------
# gnomAD
# ---------------------------------------------------------------------------

@pytest.mark.live
class TestGnomADLive:
    def setup_method(self):
        self.adapter = GnomADAdapter()

    def teardown_method(self):
        self.adapter.close()

    @_skip_on_network_error
    def test_query_variant(self):
        # Use a well-characterized variant (GBA1 region, GRCh38 coords)
        # Fallback: just verify the API responds with valid GraphQL structure
        result = self.adapter.query_variant("1-155235218-T-C")
        assert "data" in result, "Expected GraphQL data envelope"

    @_skip_on_network_error
    def test_lookup(self):
        result = self.adapter.lookup("1-155235218-T-C")
        # Variant may or may not be in gnomAD — just verify the adapter
        # roundtrips without error and returns the expected schema
        assert "found" in result
        if result["found"]:
            assert "genome_af" in result or "exome_af" in result


# ---------------------------------------------------------------------------
# PubMed
# ---------------------------------------------------------------------------

@pytest.mark.live
class TestPubMedLive:
    def setup_method(self):
        self.adapter = PubMedAdapter()

    def teardown_method(self):
        self.adapter.close()

    @_skip_on_network_error
    def test_search(self):
        result = self.adapter.search("Gaucher disease GBA1")
        id_list = result.get("esearchresult", {}).get("idlist", [])
        assert isinstance(id_list, list)
        assert len(id_list) > 0, "Expected PubMed results for Gaucher disease GBA1"

    @_skip_on_network_error
    def test_lookup(self):
        result = self.adapter.lookup("Gaucher disease GBA1")
        assert result["found"] is True
        assert result["total_results"] > 0


# ---------------------------------------------------------------------------
# Differential Diagnosis (async OpenWebUI tool)
# ---------------------------------------------------------------------------

@pytest.mark.live
class TestDiffDxLive:
    @_skip_on_network_error
    def test_differential_diagnosis(self):
        tool = DiffDxTools()
        result_json = asyncio.run(
            tool.differential_diagnosis("hepatosplenomegaly, thrombocytopenia")
        )
        result = json.loads(result_json)
        assert "differentials" in result
        assert isinstance(result["differentials"], list)
        assert "resolved_hpo_terms" in result
        assert len(result["input_symptoms"]) == 2
