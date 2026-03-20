"""Tests for regression testing module."""

from rare_archive_models.training.regression import (
    check_regression,
    generate_report,
    RegressionResult,
)


class TestCheckRegression:
    """Tests for check_regression()."""

    def test_all_metrics_pass(self, sample_current_results, sample_baseline_results):
        """When metrics are within thresholds, all checks pass."""
        checks = check_regression(sample_current_results, sample_baseline_results)
        assert all(c.passed for c in checks)

    def test_accuracy_drop_beyond_threshold(self, sample_baseline_results):
        """Accuracy drop beyond threshold fails the check."""
        current = {
            "top_1_accuracy": 0.60,  # 0.05 drop, above 0.02 threshold
            "top_5_accuracy": 0.85,
            "mean_score": 1.45,
        }
        checks = check_regression(current, sample_baseline_results)
        top1_check = next(c for c in checks if c.metric == "top_1_accuracy")
        assert not top1_check.passed

    def test_perplexity_mean_score_drop_fails(self, sample_baseline_results):
        """Large mean score drop fails the check."""
        current = {
            "top_1_accuracy": 0.65,
            "top_5_accuracy": 0.85,
            "mean_score": 1.20,  # 0.25 drop, above 0.1 threshold
        }
        checks = check_regression(current, sample_baseline_results)
        mean_check = next(c for c in checks if c.metric == "mean_score")
        assert not mean_check.passed

    def test_equal_values_pass(self, sample_baseline_results):
        """Identical baseline and current values pass all checks."""
        checks = check_regression(sample_baseline_results, sample_baseline_results)
        assert all(c.passed for c in checks)


class TestGenerateReport:
    """Tests for generate_report()."""

    def test_all_passed_report(self, sample_current_results, sample_baseline_results):
        checks = check_regression(sample_current_results, sample_baseline_results)
        report = generate_report(checks)
        assert report["passed"] is True
        assert "All regression checks passed" in report["summary"]

    def test_report_contains_all_checks(self, sample_current_results, sample_baseline_results):
        checks = check_regression(sample_current_results, sample_baseline_results)
        report = generate_report(checks)
        assert len(report["checks"]) == len(checks)
        metrics = {c["metric"] for c in report["checks"]}
        assert "top_1_accuracy" in metrics
        assert "top_5_accuracy" in metrics
        assert "mean_score" in metrics

    def test_failed_checks_set_passed_false(self, sample_baseline_results):
        current = {"top_1_accuracy": 0.40, "top_5_accuracy": 0.50, "mean_score": 0.5}
        checks = check_regression(current, sample_baseline_results)
        report = generate_report(checks)
        assert report["passed"] is False
        assert "failed" in report["summary"]


class TestEdgeCases:
    """Edge case tests for regression module."""

    def test_empty_baselines(self):
        """Empty dicts default to 0 and pass (no drop from 0)."""
        checks = check_regression({}, {})
        assert all(c.passed for c in checks)

    def test_zero_value_baselines(self):
        """Zero baselines don't cause division errors."""
        baseline = {"top_1_accuracy": 0, "top_5_accuracy": 0, "mean_score": 0}
        current = {"top_1_accuracy": 0.5, "top_5_accuracy": 0.5, "mean_score": 0.5}
        checks = check_regression(current, baseline)
        # Current is higher than baseline — no drop — should pass
        assert all(c.passed for c in checks)
