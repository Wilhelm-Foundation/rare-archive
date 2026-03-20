"""Shared fixtures for ontology package tests."""

from pathlib import Path

import pytest


@pytest.fixture
def schema_dir():
    """Path to the ontology JSON schemas directory."""
    return Path(__file__).parent.parent / "schemas"


@pytest.fixture
def valid_patient_category():
    return {
        "category_id": "rare_cat_neuromuscular",
        "name": "Neuromuscular Disorders",
        "version": "1.0.0",
        "diseases": [
            {
                "disease_id": "Orphanet_98473",
                "name": "Duchenne muscular dystrophy",
                "ordo_id": "Orphanet_98473",
                "omim_id": "310200",
                "mondo_id": "MONDO:0010679",
                "gard_id": "GARD:6291",
            }
        ],
        "phenotypic_features": [
            {"hpo_id": "HP:0003391", "term": "Gowers sign"},
        ],
    }


@pytest.fixture
def valid_clinical_tool():
    return {
        "tool_id": "rare_tool_clinvar",
        "name": "ClinVar Variant Lookup",
        "version": "1.0.0",
        "api": {
            "base_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
            "auth_type": "none",
        },
    }


@pytest.fixture
def valid_model():
    return {
        "model_id": "rare_model_qwen35_4b_sft_v1",
        "name": "Qwen3.5-4B SFT LoRA v1",
        "version": "1.0.0",
        "base_model": {
            "family": "qwen3.5",
            "size": "4b",
            "architecture": "dense",
        },
        "training_stage": {
            "stage": 1,
            "method": "sft",
        },
    }


@pytest.fixture
def valid_dataset():
    return {
        "dataset_id": "rare_dataset_rarearena_v1",
        "name": "RareArena Eval v1",
        "version": "1.0.0",
        "dataset_type": "rarearena_eval",
        "license": "CC-BY-NC-SA-4.0",
    }


@pytest.fixture
def sample_categories():
    """Two sample patient categories for assignment tests."""
    return [
        {
            "category_id": "rare_cat_neuromuscular",
            "diseases": [
                {
                    "disease_id": "Orphanet_98473",
                    "name": "Duchenne muscular dystrophy",
                    "ordo_id": "Orphanet_98473",
                    "omim_id": "310200",
                    "mondo_id": "MONDO:0010679",
                    "gard_id": "GARD:6291",
                },
                {
                    "disease_id": "Orphanet_609",
                    "name": "Becker muscular dystrophy",
                },
            ],
            "phenotypic_features": [
                {"hpo_id": "HP:0003391", "term": "Gowers sign"},
                {"hpo_id": "HP:0003560", "term": "Muscular dystrophy"},
                {"hpo_id": "HP:0001290", "term": "Generalized hypotonia"},
                {"hpo_id": "HP:0002515", "term": "Waddling gait"},
            ],
        },
        {
            "category_id": "rare_cat_metabolic",
            "diseases": [
                {
                    "disease_id": "Orphanet_79201",
                    "name": "Phenylketonuria",
                    "omim_id": "261600",
                },
            ],
            "phenotypic_features": [
                {"hpo_id": "HP:0001249", "term": "Intellectual disability"},
                {"hpo_id": "HP:0000737", "term": "Irritability"},
            ],
        },
    ]
