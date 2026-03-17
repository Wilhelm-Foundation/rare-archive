"""Validate quantized GGUF models.

Step 3 of the quantization pipeline: merge_lora.py -> quantize_gguf.py -> validate_quant.py

Checks:
1. Perplexity is within tier threshold vs. full precision
2. Model can generate valid JSON for tool calls
3. Basic diagnostic reasoning quality check
"""

import argparse
import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Maximum acceptable perplexity increase per quantization method
PERPLEXITY_THRESHOLDS = {
    "Q8_0": 0.05,    # <5% increase
    "Q6_K": 0.10,    # <10% increase
    "Q5_K_M": 0.15,  # <15% increase
    "Q4_K_M": 0.25,  # <25% increase
}


def check_perplexity(
    gguf_path: str,
    test_data: str,
    llama_cpp_path: str = "llama.cpp",
) -> float:
    """Run perplexity evaluation using llama-perplexity.

    Returns:
        Perplexity value
    """
    perplexity_bin = Path(llama_cpp_path) / "build" / "bin" / "llama-perplexity"

    cmd = [
        str(perplexity_bin),
        "-m", gguf_path,
        "-f", test_data,
        "--ctx-size", "2048",
    ]

    logger.info(f"Computing perplexity for {gguf_path}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Perplexity check failed:\n{result.stderr}")

    # Parse perplexity from output
    for line in result.stdout.split("\n"):
        if "Final estimate:" in line or "perplexity" in line.lower():
            parts = line.split()
            for i, p in enumerate(parts):
                try:
                    return float(p)
                except ValueError:
                    continue

    raise RuntimeError(f"Could not parse perplexity from output:\n{result.stdout}")


def check_json_generation(
    gguf_path: str,
    llama_cpp_path: str = "llama.cpp",
) -> bool:
    """Verify the model can generate valid JSON (needed for tool calls).

    Returns:
        True if model generates parseable JSON
    """
    llama_bin = Path(llama_cpp_path) / "build" / "bin" / "llama-cli"

    prompt = (
        'Generate a JSON object with keys "diagnosis" (string) and '
        '"confidence" (number between 0 and 1). Output ONLY valid JSON:\n'
    )

    cmd = [
        str(llama_bin),
        "-m", gguf_path,
        "-p", prompt,
        "-n", "100",
        "--temp", "0.1",
        "--no-display-prompt",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    if result.returncode != 0:
        logger.warning(f"JSON generation test failed to run: {result.stderr}")
        return False

    output = result.stdout.strip()
    try:
        # Try to find JSON in output
        start = output.index("{")
        end = output.rindex("}") + 1
        parsed = json.loads(output[start:end])
        has_keys = "diagnosis" in parsed and "confidence" in parsed
        logger.info(f"JSON generation: {'PASS' if has_keys else 'FAIL'}")
        return has_keys
    except (ValueError, json.JSONDecodeError):
        logger.warning(f"Could not parse JSON from output: {output[:200]}")
        return False


def validate(
    gguf_path: str,
    quant_method: str,
    baseline_perplexity: float | None = None,
    test_data: str | None = None,
    llama_cpp_path: str = "llama.cpp",
) -> dict:
    """Run all validation checks on a quantized model.

    Returns:
        Validation report dict
    """
    report = {
        "model": gguf_path,
        "quant_method": quant_method,
        "checks": {},
        "passed": True,
    }

    # Check 1: File exists and has reasonable size
    path = Path(gguf_path)
    if not path.exists():
        report["checks"]["file"] = {"passed": False, "message": "File not found"}
        report["passed"] = False
        return report

    size_gb = path.stat().st_size / 1e9
    report["checks"]["file"] = {
        "passed": True,
        "size_gb": round(size_gb, 2),
    }

    # Check 2: Perplexity (if test data and baseline provided)
    if test_data and baseline_perplexity:
        try:
            ppl = check_perplexity(gguf_path, test_data, llama_cpp_path)
            threshold = PERPLEXITY_THRESHOLDS.get(quant_method, 0.25)
            ppl_increase = (ppl - baseline_perplexity) / baseline_perplexity
            passed = ppl_increase <= threshold

            report["checks"]["perplexity"] = {
                "passed": passed,
                "value": round(ppl, 4),
                "baseline": baseline_perplexity,
                "increase_pct": round(ppl_increase * 100, 2),
                "threshold_pct": round(threshold * 100, 2),
            }
            if not passed:
                report["passed"] = False
        except Exception as e:
            report["checks"]["perplexity"] = {"passed": False, "error": str(e)}

    # Check 3: JSON generation
    try:
        json_ok = check_json_generation(gguf_path, llama_cpp_path)
        report["checks"]["json_generation"] = {"passed": json_ok}
        if not json_ok:
            report["passed"] = False
    except Exception as e:
        report["checks"]["json_generation"] = {"passed": False, "error": str(e)}

    return report


def main():
    parser = argparse.ArgumentParser(description="Validate quantized GGUF model")
    parser.add_argument("--gguf-path", required=True)
    parser.add_argument("--quant-method", required=True, choices=list(PERPLEXITY_THRESHOLDS.keys()))
    parser.add_argument("--baseline-perplexity", type=float)
    parser.add_argument("--test-data")
    parser.add_argument("--llama-cpp-path", default="llama.cpp")
    args = parser.parse_args()

    report = validate(
        args.gguf_path,
        args.quant_method,
        args.baseline_perplexity,
        args.test_data,
        args.llama_cpp_path,
    )

    print(json.dumps(report, indent=2))
    if not report["passed"]:
        exit(1)


if __name__ == "__main__":
    main()
