"""Tests for quantize_gguf and validate_quant modules."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from rare_archive_models.quantization.quantize_gguf import (
    QUANT_METHODS,
    TIER_DEFAULTS,
    convert_to_gguf,
    quantize_gguf,
)
from rare_archive_models.quantization.validate_quant import (
    PERPLEXITY_THRESHOLDS,
    check_perplexity,
    check_json_generation,
    validate,
)


class TestQuantMethods:
    """Tests for quantization method constants."""

    def test_quant_methods_complete(self):
        expected = {"F16", "Q8_0", "Q6_K", "Q5_K_M", "Q4_K_M"}
        assert set(QUANT_METHODS.keys()) == expected

    def test_tier_defaults(self):
        assert TIER_DEFAULTS["L1"] == "Q4_K_M"
        assert TIER_DEFAULTS["L2"] == "Q8_0"
        assert TIER_DEFAULTS["L3"] == "F16"


class TestConvertToGguf:
    """Tests for convert_to_gguf()."""

    @patch("rare_archive_models.quantization.quantize_gguf.subprocess.run")
    def test_calls_convert_script(self, mock_run, tmp_path):
        output = tmp_path / "model.gguf"
        # Create dummy file so stat() works
        output.write_text("dummy")
        mock_run.return_value = MagicMock(returncode=0)

        result = convert_to_gguf("/models/merged", str(output), "/opt/llama.cpp")

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "convert_hf_to_gguf.py" in cmd[1]
        assert "/models/merged" in cmd
        assert result == output

    @patch("rare_archive_models.quantization.quantize_gguf.subprocess.run")
    def test_raises_on_failure(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=1, stderr="conversion error")
        try:
            convert_to_gguf("/models/merged", str(tmp_path / "out.gguf"))
            assert False, "Should have raised"
        except RuntimeError as e:
            assert "conversion" in str(e).lower() or "failed" in str(e).lower()


class TestQuantizeGguf:
    """Tests for quantize_gguf()."""

    @patch("rare_archive_models.quantization.quantize_gguf.subprocess.run")
    def test_calls_quantize_with_method(self, mock_run, tmp_path):
        output = tmp_path / "model-q4.gguf"
        output.write_text("dummy")
        mock_run.return_value = MagicMock(returncode=0)

        result = quantize_gguf("/input.gguf", str(output), "Q4_K_M", "/opt/llama.cpp")

        cmd = mock_run.call_args[0][0]
        assert "Q4_K_M" in cmd
        assert result == output

    @patch("rare_archive_models.quantization.quantize_gguf.subprocess.run")
    def test_raises_on_failure(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=1, stderr="quant error")
        try:
            quantize_gguf("/input.gguf", str(tmp_path / "out.gguf"), "Q4_K_M")
            assert False, "Should have raised"
        except RuntimeError:
            pass


class TestCheckPerplexity:
    """Tests for check_perplexity()."""

    @patch("rare_archive_models.quantization.validate_quant.subprocess.run")
    def test_parses_perplexity(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="[1]1234.56\nFinal estimate: perplexity = 5.4321 +/- 0.12\n",
        )
        ppl = check_perplexity("/model.gguf", "/test.txt")
        assert isinstance(ppl, float)

    @patch("rare_archive_models.quantization.validate_quant.subprocess.run")
    def test_raises_on_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="error")
        try:
            check_perplexity("/model.gguf", "/test.txt")
            assert False, "Should have raised"
        except RuntimeError:
            pass


class TestValidate:
    """Tests for validate()."""

    def test_file_not_found(self, tmp_path):
        report = validate(str(tmp_path / "missing.gguf"), "Q4_K_M")
        assert report["passed"] is False
        assert report["checks"]["file"]["passed"] is False

    def test_file_exists_passes(self, tmp_path):
        gguf = tmp_path / "model.gguf"
        gguf.write_bytes(b"\x00" * 1024)
        report = validate(str(gguf), "Q4_K_M")
        assert report["checks"]["file"]["passed"] is True

    @patch("rare_archive_models.quantization.validate_quant.check_json_generation")
    @patch("rare_archive_models.quantization.validate_quant.check_perplexity")
    def test_perplexity_within_threshold_passes(self, mock_ppl, mock_json, tmp_path):
        gguf = tmp_path / "model.gguf"
        gguf.write_bytes(b"\x00" * 1024)
        mock_ppl.return_value = 5.5  # 10% increase from baseline 5.0
        mock_json.return_value = True

        report = validate(str(gguf), "Q4_K_M", baseline_perplexity=5.0, test_data="/test.txt")
        assert report["checks"]["perplexity"]["passed"] is True
        assert report["passed"] is True

    @patch("rare_archive_models.quantization.validate_quant.check_json_generation")
    @patch("rare_archive_models.quantization.validate_quant.check_perplexity")
    def test_perplexity_beyond_threshold_fails(self, mock_ppl, mock_json, tmp_path):
        gguf = tmp_path / "model.gguf"
        gguf.write_bytes(b"\x00" * 1024)
        mock_ppl.return_value = 10.0  # 100% increase from baseline 5.0
        mock_json.return_value = True

        report = validate(str(gguf), "Q4_K_M", baseline_perplexity=5.0, test_data="/test.txt")
        assert report["checks"]["perplexity"]["passed"] is False
        assert report["passed"] is False

    def test_report_format(self, tmp_path):
        gguf = tmp_path / "model.gguf"
        gguf.write_bytes(b"\x00" * 1024)
        report = validate(str(gguf), "Q4_K_M")
        assert "model" in report
        assert "quant_method" in report
        assert "checks" in report
        assert "passed" in report
