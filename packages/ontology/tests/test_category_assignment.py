"""Tests for rare_archive_ontology.category_assignment."""

from rare_archive_ontology.category_assignment import (
    assign_by_disease_id,
    assign_by_phenotype_overlap,
    compute_coverage,
)


class TestAssignByDiseaseId:
    def test_match_disease_id(self, sample_categories):
        result = assign_by_disease_id("Orphanet_98473", sample_categories)
        assert result == "rare_cat_neuromuscular"

    def test_match_omim_id(self, sample_categories):
        result = assign_by_disease_id("310200", sample_categories)
        assert result == "rare_cat_neuromuscular"

    def test_match_mondo_id(self, sample_categories):
        result = assign_by_disease_id("MONDO:0010679", sample_categories)
        assert result == "rare_cat_neuromuscular"

    def test_match_gard_id(self, sample_categories):
        result = assign_by_disease_id("GARD:6291", sample_categories)
        assert result == "rare_cat_neuromuscular"

    def test_match_second_category(self, sample_categories):
        result = assign_by_disease_id("261600", sample_categories)
        assert result == "rare_cat_metabolic"

    def test_no_match(self, sample_categories):
        result = assign_by_disease_id("UNKNOWN:99999", sample_categories)
        assert result is None

    def test_empty_categories(self):
        result = assign_by_disease_id("Orphanet_98473", [])
        assert result is None


class TestAssignByPhenotypeOverlap:
    def test_high_overlap(self, sample_categories):
        # Query 3 of 4 neuromuscular HPO terms → Jaccard = 3/(4+0) = 3/4 = 0.75
        query = ["HP:0003391", "HP:0003560", "HP:0001290"]
        results = assign_by_phenotype_overlap(query, sample_categories)
        assert len(results) > 0
        assert results[0][0] == "rare_cat_neuromuscular"
        assert results[0][1] > 0.5

    def test_below_min_overlap_filtered(self, sample_categories):
        # Query with 1 shared term out of many unique → low Jaccard
        query = ["HP:0003391", "HP:9999901", "HP:9999902", "HP:9999903", "HP:9999904"]
        results = assign_by_phenotype_overlap(query, sample_categories, min_overlap=0.5)
        cat_ids = [r[0] for r in results]
        assert "rare_cat_neuromuscular" not in cat_ids

    def test_sorted_by_descending_score(self, sample_categories):
        # Query that overlaps with both categories
        query = ["HP:0003391", "HP:0001249"]
        results = assign_by_phenotype_overlap(query, sample_categories, min_overlap=0.0)
        if len(results) >= 2:
            assert results[0][1] >= results[1][1]

    def test_no_overlap_returns_empty(self, sample_categories):
        query = ["HP:9999999"]
        results = assign_by_phenotype_overlap(query, sample_categories)
        assert results == []

    def test_empty_categories(self):
        results = assign_by_phenotype_overlap(["HP:0003391"], [])
        assert results == []


class TestComputeCoverage:
    def test_all_assigned(self, sample_categories):
        disease_ids = ["Orphanet_98473", "261600"]
        result = compute_coverage(disease_ids, sample_categories)
        assert result["total_diseases"] == 2
        assert result["assigned_count"] == 2
        assert result["unassigned_count"] == 0
        assert result["coverage_pct"] == 100.0
        assert result["unassigned_ids"] == []

    def test_partial_coverage(self, sample_categories):
        disease_ids = ["Orphanet_98473", "UNKNOWN:99999"]
        result = compute_coverage(disease_ids, sample_categories)
        assert result["total_diseases"] == 2
        assert result["assigned_count"] == 1
        assert result["unassigned_count"] == 1
        assert result["coverage_pct"] == 50.0
        assert result["unassigned_ids"] == ["UNKNOWN:99999"]

    def test_none_assigned(self, sample_categories):
        disease_ids = ["UNKNOWN:1", "UNKNOWN:2"]
        result = compute_coverage(disease_ids, sample_categories)
        assert result["assigned_count"] == 0
        assert result["coverage_pct"] == 0.0

    def test_empty_disease_list(self, sample_categories):
        result = compute_coverage([], sample_categories)
        assert result["total_diseases"] == 0
        assert result["coverage_pct"] == 0
