"""Tests for category mapper."""

import json

import pytest

from rare_archive_datasets.assignment.category_mapper import (
    CategoryMapping,
    load_category_index,
    map_batch,
    map_case,
)
from rare_archive_datasets.ingestion.rarearena import RareArenaCase


class TestLoadCategoryIndex:
    def test_returns_expected_keys(self, sample_category_dir):
        index = load_category_index(sample_category_dir)
        assert "categories" in index
        assert "disease_index" in index
        assert "phenotype_index" in index

    def test_disease_index_maps_all_id_types(self, sample_category_dir):
        index = load_category_index(sample_category_dir)
        di = index["disease_index"]
        assert di["ORPHA:558"] == "cat_neuro"
        assert di["154700"] == "cat_neuro"
        assert di["ORPHA:324"] == "cat_cardio"
        assert di["MONDO:0010001"] == "cat_cardio"

    def test_phenotype_index_maps_hpo_ids(self, sample_category_dir):
        index = load_category_index(sample_category_dir)
        pi = index["phenotype_index"]
        assert "HP:0001250" in pi
        assert "cat_neuro" in pi["HP:0001250"]


class TestMapCase:
    def test_disease_id_exact_match(self, sample_category_dir):
        index = load_category_index(sample_category_dir)
        case = RareArenaCase(
            case_id="1", clinical_vignette="v", ground_truth_diagnosis="d",
            disease_id="ORPHA:558",
        )
        mapping = map_case(case, index)
        assert mapping.category_id == "cat_neuro"
        assert mapping.match_method == "disease_id"
        assert mapping.confidence == 1.0

    def test_phenotype_overlap_match(self, sample_category_dir):
        index = load_category_index(sample_category_dir)
        case = RareArenaCase(
            case_id="2", clinical_vignette="v", ground_truth_diagnosis="d",
            hpo_terms=["HP:0001250", "HP:0001252"],
        )
        mapping = map_case(case, index)
        assert mapping.category_id == "cat_neuro"
        assert mapping.match_method == "phenotype_overlap"
        assert mapping.confidence > 0.0

    def test_below_threshold_unmatched(self, sample_category_dir):
        index = load_category_index(sample_category_dir)
        # One HPO match out of 10 query terms → Jaccard well below 0.5
        case = RareArenaCase(
            case_id="3", clinical_vignette="v", ground_truth_diagnosis="d",
            hpo_terms=[
                "HP:0001250", "HP:9999991", "HP:9999992", "HP:9999993",
                "HP:9999994", "HP:9999995", "HP:9999996", "HP:9999997",
                "HP:9999998", "HP:9999999",
            ],
        )
        mapping = map_case(case, index, min_phenotype_overlap=0.5)
        assert mapping.category_id is None
        assert mapping.match_method == "unmatched"

    def test_no_disease_no_hpo_unmatched(self, sample_category_dir):
        index = load_category_index(sample_category_dir)
        case = RareArenaCase(
            case_id="4", clinical_vignette="v", ground_truth_diagnosis="d",
        )
        mapping = map_case(case, index)
        assert mapping.category_id is None
        assert mapping.match_method == "unmatched"

    def test_candidate_categories_ranked_descending(self, sample_category_dir):
        index = load_category_index(sample_category_dir)
        # Terms that overlap with both categories
        case = RareArenaCase(
            case_id="5", clinical_vignette="v", ground_truth_diagnosis="d",
            hpo_terms=["HP:0001250", "HP:0001252", "HP:0001635"],
        )
        mapping = map_case(case, index, min_phenotype_overlap=0.1)
        if len(mapping.candidate_categories) > 1:
            scores = [s for _, s in mapping.candidate_categories]
            assert scores == sorted(scores, reverse=True)


class TestMapBatch:
    def test_returns_list_of_mappings(self, sample_category_dir):
        cases = [
            RareArenaCase(
                case_id="1", clinical_vignette="v", ground_truth_diagnosis="d",
                disease_id="ORPHA:558",
            ),
            RareArenaCase(case_id="2", clinical_vignette="v", ground_truth_diagnosis="d"),
        ]
        mappings = map_batch(cases, sample_category_dir)
        assert len(mappings) == 2
        assert all(isinstance(m, CategoryMapping) for m in mappings)

    def test_sets_patient_category_on_matched(self, sample_category_dir):
        case = RareArenaCase(
            case_id="1", clinical_vignette="v", ground_truth_diagnosis="d",
            disease_id="ORPHA:558",
        )
        map_batch([case], sample_category_dir)
        assert case.patient_category == "cat_neuro"

    def test_mixed_matched_unmatched(self, sample_category_dir):
        cases = [
            RareArenaCase(
                case_id="1", clinical_vignette="v", ground_truth_diagnosis="d",
                disease_id="ORPHA:558",
            ),
            RareArenaCase(case_id="2", clinical_vignette="v", ground_truth_diagnosis="d"),
        ]
        mappings = map_batch(cases, sample_category_dir)
        assert mappings[0].category_id == "cat_neuro"
        assert mappings[1].category_id is None
