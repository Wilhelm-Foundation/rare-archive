"""Tests for rare_archive_compliance.fair_scorer."""

from rare_archive_compliance.fair_scorer import FAIRCategory, score_artifact


class TestScoreArtifactFullyCompliant:
    def test_score_100(self, fully_compliant_metadata):
        result = score_artifact(fully_compliant_metadata)
        assert result["total_score"] == 100
        assert result["publication_ready"] is True

    def test_all_criteria_pass(self, fully_compliant_metadata):
        result = score_artifact(fully_compliant_metadata)
        for r in result["results"]:
            assert r["passed"] is True, f"{r['id']} failed: {r['message']}"


class TestScoreArtifactMinimal:
    def test_low_score(self, minimal_metadata):
        result = score_artifact(minimal_metadata)
        assert result["total_score"] < 50

    def test_not_publication_ready(self, minimal_metadata):
        result = score_artifact(minimal_metadata)
        assert result["publication_ready"] is False


class TestPublicationReadiness:
    """Required criteria: F2, R1, RA-F1, RA-I1, RA-R1."""

    def _metadata_passing_required(self):
        """Metadata that passes exactly the 5 required criteria."""
        return {
            "name": "test_artifact",
            "description": "A sufficiently long description for FAIR F2",
            "version": "1.0.0",
            "license": "Apache-2.0",
            "category_id": "rare_cat_test",
            "adna": {
                "type": "rare_clinical_tool",
                "namespace": "rare_",
                "triad": "what",
            },
        }

    def test_all_required_pass(self):
        result = score_artifact(self._metadata_passing_required())
        assert result["publication_ready"] is True

    def test_missing_f2_blocks_publication(self):
        data = self._metadata_passing_required()
        del data["description"]
        result = score_artifact(data)
        assert result["publication_ready"] is False

    def test_missing_r1_blocks_publication(self):
        data = self._metadata_passing_required()
        del data["license"]
        result = score_artifact(data)
        assert result["publication_ready"] is False

    def test_missing_ra_f1_blocks_publication(self):
        data = self._metadata_passing_required()
        del data["category_id"]
        result = score_artifact(data)
        assert result["publication_ready"] is False

    def test_missing_ra_i1_blocks_publication(self):
        data = self._metadata_passing_required()
        del data["adna"]
        result = score_artifact(data)
        assert result["publication_ready"] is False


class TestDatasetPHIGovernance:
    def test_dataset_without_phi_status_fails_ra_r1(self):
        data = {
            "name": "test_dataset",
            "adna": {"type": "rare_dataset", "namespace": "rare_", "triad": "what"},
        }
        result = score_artifact(data)
        ra_r1 = next(r for r in result["results"] if r["id"] == "RA-R1")
        assert ra_r1["passed"] is False

    def test_dataset_with_phi_status_passes_ra_r1(self):
        data = {
            "name": "test_dataset",
            "adna": {"type": "rare_dataset", "namespace": "rare_", "triad": "what"},
            "consent": {"phi_status": "synthetic_only"},
        }
        result = score_artifact(data)
        ra_r1 = next(r for r in result["results"] if r["id"] == "RA-R1")
        assert ra_r1["passed"] is True

    def test_non_dataset_gets_ra_r1_pass(self):
        data = {
            "name": "test_model",
            "adna": {"type": "rare_model", "namespace": "rare_", "triad": "what"},
        }
        result = score_artifact(data)
        ra_r1 = next(r for r in result["results"] if r["id"] == "RA-R1")
        assert ra_r1["passed"] is True
        assert "N/A" in ra_r1["message"]


class TestModelTrainingProvenance:
    def test_model_without_lineage_fails_ra_r2(self):
        data = {
            "name": "test_model",
            "adna": {"type": "rare_model", "namespace": "rare_", "triad": "what"},
        }
        result = score_artifact(data)
        ra_r2 = next(r for r in result["results"] if r["id"] == "RA-R2")
        assert ra_r2["passed"] is False

    def test_model_with_lineage_passes_ra_r2(self):
        data = {
            "name": "test_model",
            "adna": {"type": "rare_model", "namespace": "rare_", "triad": "what"},
            "lineage": {"parent_model_id": "rare_model_base_v1"},
        }
        result = score_artifact(data)
        ra_r2 = next(r for r in result["results"] if r["id"] == "RA-R2")
        assert ra_r2["passed"] is True

    def test_non_model_gets_ra_r2_pass(self):
        data = {
            "name": "test_tool",
            "adna": {"type": "rare_clinical_tool", "namespace": "rare_", "triad": "what"},
        }
        result = score_artifact(data)
        ra_r2 = next(r for r in result["results"] if r["id"] == "RA-R2")
        assert ra_r2["passed"] is True


class TestByCategoryBreakdown:
    def test_categories_present(self, fully_compliant_metadata):
        result = score_artifact(fully_compliant_metadata)
        for cat in FAIRCategory:
            assert cat.value in result["by_category"]

    def test_category_earned_lte_total(self, fully_compliant_metadata):
        result = score_artifact(fully_compliant_metadata)
        for cat_data in result["by_category"].values():
            assert cat_data["earned"] <= cat_data["total"]

    def test_category_scores_sum_to_total(self, fully_compliant_metadata):
        result = score_artifact(fully_compliant_metadata)
        total_earned = sum(c["earned"] for c in result["by_category"].values())
        assert abs(total_earned - result["earned_weight"]) < 0.01
