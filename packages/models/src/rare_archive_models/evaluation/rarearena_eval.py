"""RareArena evaluation harness.

3-step evaluation protocol:
1. Generate: Model produces top-5 differential diagnoses for each case
2. Score: GPT-4o judges each diagnosis (0=wrong, 1=partial, 2=correct)
3. Metrics: Compute top-1 accuracy, top-5 accuracy, mean score

Pre-computed GPT-4o baselines can be stored as static JSON to avoid repeated API costs.
"""

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EvalCase:
    """A single evaluation case."""
    case_id: str
    clinical_vignette: str
    ground_truth: str
    disease_id: str | None = None
    patient_category: str | None = None


@dataclass
class EvalResult:
    """Result of evaluating a single case."""
    case_id: str
    ground_truth: str
    generated_diagnoses: list[str]
    scores: list[int]  # 0, 1, or 2 for each diagnosis
    top_1_correct: bool
    top_5_correct: bool
    best_score: int


def load_eval_cases(path: Path, max_cases: int | None = None) -> list[EvalCase]:
    """Load evaluation cases from JSONL."""
    cases = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            cases.append(EvalCase(
                case_id=data.get("case_id", str(len(cases))),
                clinical_vignette=data.get("clinical_vignette", data.get("input", "")),
                ground_truth=data.get("ground_truth_diagnosis", data.get("output", "")),
                disease_id=data.get("disease_id"),
                patient_category=data.get("patient_category"),
            ))
            if max_cases and len(cases) >= max_cases:
                break
    return cases


def generate_diagnoses(
    case: EvalCase,
    model_fn: Any,
    n_diagnoses: int = 5,
) -> list[str]:
    """Generate top-N differential diagnoses using the model.

    Args:
        case: Evaluation case
        model_fn: Callable that takes a prompt string and returns a response string
        n_diagnoses: Number of diagnoses to generate

    Returns:
        List of diagnosis strings
    """
    prompt = (
        f"You are an expert rare disease diagnostician. Given the following clinical "
        f"presentation, provide your top {n_diagnoses} differential diagnoses. "
        f"List each diagnosis on its own line, numbered 1-{n_diagnoses}.\n\n"
        f"Clinical Presentation:\n{case.clinical_vignette}\n\n"
        f"Top {n_diagnoses} Differential Diagnoses:"
    )

    response = model_fn(prompt)
    diagnoses = _parse_diagnoses(response, n_diagnoses)

    return diagnoses


def _parse_diagnoses(response: str, max_n: int) -> list[str]:
    """Parse numbered diagnoses from model response."""
    diagnoses = []
    for line in response.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        # Remove numbering (1., 1), 1:, etc.)
        cleaned = line.lstrip("0123456789").lstrip(".):- ").strip()
        if cleaned:
            diagnoses.append(cleaned)
        if len(diagnoses) >= max_n:
            break
    return diagnoses


def score_diagnosis(
    diagnosis: str,
    ground_truth: str,
    scorer_fn: Any | None = None,
) -> int:
    """Score a single diagnosis against ground truth.

    Returns:
        0 = incorrect
        1 = partially correct (related condition, correct disease family)
        2 = correct (matches ground truth)

    If scorer_fn is None, uses exact string matching.
    If scorer_fn is provided, it should be a callable that takes
    (diagnosis, ground_truth) and returns 0, 1, or 2.
    """
    if scorer_fn:
        return scorer_fn(diagnosis, ground_truth)

    # Simple exact match fallback
    d_lower = diagnosis.lower().strip()
    gt_lower = ground_truth.lower().strip()

    if d_lower == gt_lower or gt_lower in d_lower or d_lower in gt_lower:
        return 2

    # Check for word overlap (partial credit)
    d_words = set(d_lower.split())
    gt_words = set(gt_lower.split())
    overlap = len(d_words & gt_words) / max(len(gt_words), 1)
    if overlap >= 0.5:
        return 1

    return 0


def evaluate_case(
    case: EvalCase,
    model_fn: Any,
    scorer_fn: Any | None = None,
    n_diagnoses: int = 5,
) -> EvalResult:
    """Evaluate a single case end-to-end: generate -> score -> result."""
    diagnoses = generate_diagnoses(case, model_fn, n_diagnoses)
    scores = [score_diagnosis(d, case.ground_truth, scorer_fn) for d in diagnoses]

    # Pad if fewer diagnoses generated
    while len(scores) < n_diagnoses:
        scores.append(0)
        diagnoses.append("")

    top_1_correct = scores[0] == 2 if scores else False
    top_5_correct = any(s == 2 for s in scores)
    best_score = max(scores) if scores else 0

    return EvalResult(
        case_id=case.case_id,
        ground_truth=case.ground_truth,
        generated_diagnoses=diagnoses,
        scores=scores,
        top_1_correct=top_1_correct,
        top_5_correct=top_5_correct,
        best_score=best_score,
    )


def evaluate_batch(
    cases: list[EvalCase],
    model_fn: Any,
    scorer_fn: Any | None = None,
    n_diagnoses: int = 5,
) -> dict[str, Any]:
    """Evaluate a batch of cases and compute aggregate metrics."""
    results = []
    for i, case in enumerate(cases):
        result = evaluate_case(case, model_fn, scorer_fn, n_diagnoses)
        results.append(result)
        if (i + 1) % 50 == 0:
            logger.info(f"Evaluated {i+1}/{len(cases)} cases")

    metrics = compute_metrics(results)
    metrics["results"] = [
        {
            "case_id": r.case_id,
            "ground_truth": r.ground_truth,
            "diagnoses": r.generated_diagnoses,
            "scores": r.scores,
            "top_1_correct": r.top_1_correct,
            "top_5_correct": r.top_5_correct,
        }
        for r in results
    ]

    return metrics


def compute_metrics(results: list[EvalResult]) -> dict[str, Any]:
    """Compute aggregate metrics from evaluation results."""
    if not results:
        return {"top_1_accuracy": 0, "top_5_accuracy": 0, "mean_score": 0, "n_cases": 0}

    n = len(results)
    top_1_acc = sum(1 for r in results if r.top_1_correct) / n
    top_5_acc = sum(1 for r in results if r.top_5_correct) / n
    mean_score = sum(r.best_score for r in results) / n

    # Per-category breakdown
    by_category: dict[str, list[EvalResult]] = {}
    for r in results:
        # Category comes from the eval case, stored in results
        cat = "unknown"
        by_category.setdefault(cat, []).append(r)

    return {
        "top_1_accuracy": round(top_1_acc, 4),
        "top_5_accuracy": round(top_5_acc, 4),
        "mean_score": round(mean_score, 4),
        "n_cases": n,
        "top_1_count": sum(1 for r in results if r.top_1_correct),
        "top_5_count": sum(1 for r in results if r.top_5_correct),
    }


def save_results(metrics: dict[str, Any], output_path: Path):
    """Save evaluation results to JSON."""
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    logger.info(f"Results saved to {output_path}")


def load_baseline(baseline_path: Path) -> dict[str, Any]:
    """Load pre-computed baseline results (e.g., GPT-4o)."""
    with open(baseline_path) as f:
        return json.load(f)
