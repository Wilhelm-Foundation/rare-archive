"""Shared fixtures for datasets tests."""

import json

import pytest

from rare_archive_datasets.ingestion.rarearena import RareArenaCase
from rare_archive_datasets.synthetic.patient_generator import DiseaseProfile


@pytest.fixture
def v1_record():
    """Sample v1 format JSONL record."""
    return {
        "case_id": "rds_001",
        "input": "A 12-year-old boy presents with tall stature and arachnodactyly.",
        "output": "Marfan syndrome",
        "disease_id": "ORPHA:558",
        "hpo_terms": ["HP:0001166", "HP:0001519"],
    }


@pytest.fixture
def v2_record():
    """Sample v2 format JSONL record."""
    return {
        "clinical_note": "A 5-year-old girl with progressive renal failure.",
        "diagnosis": "Fabry disease",
        "orpha_code": "ORPHA:324",
        "phenotypes": ["HP:0000083", "HP:0007957"],
    }


@pytest.fixture
def sample_cases():
    """Pre-built list of RareArenaCase objects."""
    return [
        RareArenaCase(
            case_id="rds_001",
            clinical_vignette="Patient with tall stature.",
            ground_truth_diagnosis="Marfan syndrome",
            disease_id="ORPHA:558",
            hpo_terms=["HP:0001166", "HP:0001519"],
            split="rds",
        ),
        RareArenaCase(
            case_id="rds_002",
            clinical_vignette="Child with seizures.",
            ground_truth_diagnosis="Dravet syndrome",
            disease_id="ORPHA:33069",
            hpo_terms=["HP:0001250"],
            split="rds",
        ),
        RareArenaCase(
            case_id="rdc_001",
            clinical_vignette="Infant with progressive renal failure.",
            ground_truth_diagnosis="Fabry disease",
            disease_id="ORPHA:324",
            split="rdc",
        ),
    ]


@pytest.fixture
def sample_category_dir(tmp_path):
    """Directory with 2 sample category JSON files."""
    cat1 = {
        "category_id": "cat_neuro",
        "diseases": [
            {"disease_id": "ORPHA:558", "omim_id": "154700"},
            {"disease_id": "ORPHA:33069"},
        ],
        "phenotypic_features": [
            {"hpo_id": "HP:0001250"},
            {"hpo_id": "HP:0001252"},
            {"hpo_id": "HP:0002066"},
        ],
    }
    cat2 = {
        "category_id": "cat_cardio",
        "diseases": [
            {"disease_id": "ORPHA:324", "mondo_id": "MONDO:0010001"},
        ],
        "phenotypic_features": [
            {"hpo_id": "HP:0001635"},
            {"hpo_id": "HP:0004756"},
        ],
    }
    (tmp_path / "neuro.json").write_text(json.dumps(cat1))
    (tmp_path / "cardio.json").write_text(json.dumps(cat2))
    return tmp_path


@pytest.fixture
def disease_profile():
    """Sample DiseaseProfile for synthetic patient generation."""
    return DiseaseProfile(
        disease_id="ORPHA:558",
        disease_name="Marfan syndrome",
        ordo_id="558",
        hpo_phenotypes=[
            {"hpo_id": "HP:0001166", "term": "Arachnodactyly", "frequency": "obligate"},
            {"hpo_id": "HP:0001519", "term": "Disproportionate tall stature", "frequency": "very_frequent"},
            {"hpo_id": "HP:0000268", "term": "Dolichocephaly", "frequency": "frequent"},
            {"hpo_id": "HP:0002996", "term": "Limited elbow extension", "frequency": "excluded"},
        ],
        inheritance_patterns=["autosomal_dominant"],
        age_of_onset=["childhood"],
        patient_category="cat_neuro",
    )
