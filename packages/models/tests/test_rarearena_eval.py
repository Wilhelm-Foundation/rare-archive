"""Tests for the RareArena evaluation harness."""

import json

from rare_archive_models.evaluation.rarearena_eval import (
    EvalCase,
    EvalResult,
    load_eval_cases,
    _parse_diagnoses,
    score_diagnosis,
    compute_metrics,
    save_results,
    load_baseline,
)


class TestLoadEvalCases:
    """Tests for load_eval_cases()."""

    def test_valid_jsonl(self, sample_eval_cases, jsonl_file):
        path = jsonl_file(sample_eval_cases, "eval.jsonl")
        cases = load_eval_cases(path)
        assert len(cases) == 2
        assert cases[0].case_id == "CASE001"
        assert cases[0].ground_truth == "Duchenne muscular dystrophy"

    def test_max_cases_limit(self, sample_eval_cases, jsonl_file):
        path = jsonl_file(sample_eval_cases, "eval.jsonl")
        cases = load_eval_cases(path, max_cases=1)
        assert len(cases) == 1

    def test_empty_file(self, tmp_path):
        path = tmp_path / "empty.jsonl"
        path.write_text("")
        cases = load_eval_cases(path)
        assert cases == []


class TestParseDiagnoses:
    """Tests for _parse_diagnoses()."""

    def test_numbered_list(self):
        response = "1. Duchenne muscular dystrophy\n2. Becker muscular dystrophy\n3. SMA"
        result = _parse_diagnoses(response, 5)
        assert len(result) == 3
        assert result[0] == "Duchenne muscular dystrophy"

    def test_mixed_formats(self):
        response = "1) Duchenne\n2: Becker\n3- SMA\n4. Myopathy"
        result = _parse_diagnoses(response, 5)
        assert len(result) == 4
        assert result[0] == "Duchenne"

    def test_single_diagnosis(self):
        response = "1. Duchenne muscular dystrophy"
        result = _parse_diagnoses(response, 5)
        assert len(result) == 1

    def test_empty_response(self):
        result = _parse_diagnoses("", 5)
        assert result == []


class TestScoreDiagnosis:
    """Tests for score_diagnosis()."""

    def test_exact_match(self):
        score = score_diagnosis("Duchenne muscular dystrophy", "Duchenne muscular dystrophy")
        assert score == 2

    def test_partial_overlap(self):
        """Significant word overlap gives partial credit."""
        score = score_diagnosis("muscular dystrophy type unknown", "Duchenne muscular dystrophy")
        assert score == 1

    def test_no_match(self):
        score = score_diagnosis("common cold", "Duchenne muscular dystrophy")
        assert score == 0

    def test_custom_scorer_fn(self):
        """Custom scorer function is called instead of default matching."""
        custom = lambda d, gt: 2
        score = score_diagnosis("anything", "anything else", scorer_fn=custom)
        assert score == 2


class TestComputeMetrics:
    """Tests for compute_metrics()."""

    def test_top1_accuracy(self):
        results = [
            EvalResult("C1", "DMD", ["DMD", "BMD"], [2, 1], True, True, 2),
            EvalResult("C2", "SMA", ["X", "SMA"], [0, 2], False, True, 2),
        ]
        metrics = compute_metrics(results)
        assert metrics["top_1_accuracy"] == 0.5

    def test_top5_accuracy(self):
        results = [
            EvalResult("C1", "DMD", ["DMD"], [2], True, True, 2),
            EvalResult("C2", "SMA", ["X", "SMA"], [0, 2], False, True, 2),
        ]
        metrics = compute_metrics(results)
        assert metrics["top_5_accuracy"] == 1.0

    def test_mean_score(self):
        results = [
            EvalResult("C1", "DMD", ["DMD"], [2], True, True, 2),
            EvalResult("C2", "SMA", ["X"], [0], False, False, 0),
        ]
        metrics = compute_metrics(results)
        assert metrics["mean_score"] == 1.0


class TestSaveAndLoadResults:
    """Tests for save_results() and load_baseline()."""

    def test_round_trip(self, tmp_path):
        metrics = {"top_1_accuracy": 0.65, "top_5_accuracy": 0.85, "mean_score": 1.45}
        path = tmp_path / "results.json"
        save_results(metrics, path)
        loaded = load_baseline(path)
        assert loaded == metrics

    def test_baseline_loading(self, tmp_path):
        data = {"top_1_accuracy": 0.70, "n_cases": 200}
        path = tmp_path / "baseline.json"
        path.write_text(json.dumps(data))
        loaded = load_baseline(path)
        assert loaded["top_1_accuracy"] == 0.70
        assert loaded["n_cases"] == 200
