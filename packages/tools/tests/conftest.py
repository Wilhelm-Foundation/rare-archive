"""Shared fixtures for tools tests."""

import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def no_sleep():
    """Prevent real sleeps in rate limiting and retries."""
    with patch("rare_archive_tools.adapters.base.time.sleep"):
        yield


@pytest.fixture
def esearch_response():
    return {
        "esearchresult": {
            "count": "1",
            "retmax": "10",
            "idlist": ["12345"],
        }
    }


@pytest.fixture
def esearch_empty_response():
    return {
        "esearchresult": {
            "count": "0",
            "retmax": "10",
            "idlist": [],
        }
    }


@pytest.fixture
def efetch_response():
    return {
        "result": {
            "12345": {
                "uid": "12345",
                "title": "NM_000546.6:c.215C>G",
                "clinical_significance": "Pathogenic",
            }
        }
    }


@pytest.fixture
def hpo_search_response():
    return {
        "terms": [
            {"id": "HP:0001250", "name": "Seizure"},
            {"id": "HP:0001252", "name": "Hypotonia"},
        ]
    }


@pytest.fixture
def hpo_term_response():
    return {
        "id": "HP:0001250",
        "name": "Seizure",
        "definition": "An episodic abnormality...",
        "synonyms": ["Epileptic seizure"],
    }


@pytest.fixture
def orphanet_search_response():
    return {
        "results": [
            {"orphaCode": 558, "name": "Marfan syndrome", "id": "558"},
        ]
    }


@pytest.fixture
def orphanet_disease_response():
    return {
        "orphaCode": 558,
        "name": "Marfan syndrome",
        "definition": "A systemic connective tissue disorder...",
    }


@pytest.fixture
def orphanet_genes_response():
    return {
        "genes": [
            {"symbol": "FBN1", "name": "fibrillin-1"},
        ]
    }


@pytest.fixture
def gnomad_variant_response():
    return {
        "data": {
            "variant": {
                "variant_id": "1-55505647-C-T",
                "rsids": ["rs28934578"],
                "genome": {"ac": 10, "an": 100000, "af": 0.0001, "populations": []},
                "exome": {"ac": 5, "an": 50000, "af": 0.0001, "populations": []},
            }
        }
    }


@pytest.fixture
def gnomad_empty_response():
    return {"data": {"variant": None}}


@pytest.fixture
def panelapp_search_response():
    return {
        "count": 1,
        "results": [
            {
                "id": 1,
                "name": "Intellectual disability",
                "disease_group": "Neurology",
                "stats": {"number_of_genes": 42},
                "version": "3.0",
            }
        ],
    }


@pytest.fixture
def panelapp_panel_response():
    return {
        "id": 1,
        "name": "Intellectual disability",
        "genes": [
            {"gene_data": {"gene_symbol": "MECP2"}, "confidence_level": "3"},
        ],
    }


@pytest.fixture
def panelapp_genes_response():
    return {
        "count": 1,
        "results": [
            {
                "gene_data": {"gene_symbol": "MECP2"},
                "panel": {"id": 1, "name": "Intellectual disability"},
            },
        ],
    }
