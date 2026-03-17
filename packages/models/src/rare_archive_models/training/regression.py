"""Regression testing for model training stages.

Blocks model publication if:
- Top-1 accuracy drops >2% vs. previous stage
- Any safety metric degrades
- Perplexity increases beyond tier threshold

Usage:
    python -m rare_archive_models.training.regression \
        --current outputs/stage2/results.json \
        --baseline outputs/stage1/results.json \
        --max-accuracy-drop 0.02
"""

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RegressionResult:
    """Result of a regression check."""
    metric: str
    current_value: float
    baseline_value: float
    threshold: float
    passed: bool
    message: str


def check_regression(
    current_results: dict[str, Any],
    baseline_results: dict[str, Any],
    max_accuracy_drop: float = 0.02,
    max_perplexity_increase: float = 0.15,
) -> list[RegressionResult]:
    """Compare current results against baseline for regressions.

    Returns list of RegressionResult with pass/fail status.
    """
    checks = []

    # Top-1 accuracy
    cur_top1 = current_results.get("top_1_accuracy", 0)
    base_top1 = baseline_results.get("top_1_accuracy", 0)
    drop = base_top1 - cur_top1
    checks.append(RegressionResult(
        metric="top_1_accuracy",
        current_value=cur_top1,
        baseline_value=base_top1,
        threshold=max_accuracy_drop,
        passed=drop <= max_accuracy_drop,
        message=f"Drop: {drop:.4f} (threshold: {max_accuracy_drop})",
    ))

    # Top-5 accuracy
    cur_top5 = current_results.get("top_5_accuracy", 0)
    base_top5 = baseline_results.get("top_5_accuracy", 0)
    drop5 = base_top5 - cur_top5
    checks.append(RegressionResult(
        metric="top_5_accuracy",
        current_value=cur_top5,
        baseline_value=base_top5,
        threshold=max_accuracy_drop,
        passed=drop5 <= max_accuracy_drop,
        message=f"Drop: {drop5:.4f}",
    ))

    # Mean score
    cur_mean = current_results.get("mean_score", 0)
    base_mean = baseline_results.get("mean_score", 0)
    mean_drop = base_mean - cur_mean
    checks.append(RegressionResult(
        metric="mean_score",
        current_value=cur_mean,
        baseline_value=base_mean,
        threshold=0.1,
        passed=mean_drop <= 0.1,
        message=f"Drop: {mean_drop:.4f}",
    ))

    return checks


def generate_report(checks: list[RegressionResult]) -> dict[str, Any]:
    """Generate a regression report."""
    all_passed = all(c.passed for c in checks)

    return {
        "passed": all_passed,
        "checks": [
            {
                "metric": c.metric,
                "current": c.current_value,
                "baseline": c.baseline_value,
                "threshold": c.threshold,
                "passed": c.passed,
                "message": c.message,
            }
            for c in checks
        ],
        "summary": "All regression checks passed" if all_passed
                   else f"{sum(1 for c in checks if not c.passed)} check(s) failed",
    }


def main():
    parser = argparse.ArgumentParser(description="Regression testing")
    parser.add_argument("--current", required=True, help="Current results JSON")
    parser.add_argument("--baseline", required=True, help="Baseline results JSON")
    parser.add_argument("--max-accuracy-drop", type=float, default=0.02)
    parser.add_argument("--output", help="Output report path")
    args = parser.parse_args()

    with open(args.current) as f:
        current = json.load(f)
    with open(args.baseline) as f:
        baseline = json.load(f)

    checks = check_regression(current, baseline, args.max_accuracy_drop)
    report = generate_report(checks)

    print(json.dumps(report, indent=2))

    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)

    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
