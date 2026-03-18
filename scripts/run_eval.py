"""Evaluate a model (optionally with LoRA adapter) on RareArena eval data.

Bridges the chat-format eval JSONL (messages array) with the rarearena_eval
harness which expects clinical_vignette / ground_truth_diagnosis fields.

Usage:
    # Baseline (no adapter)
    python scripts/run_eval.py \
        --model Qwen/Qwen3.5-4B \
        --eval-data data/rarearena_eval_rds.jsonl \
        --max-cases 200 --output outputs/eval_base_rds_200.json

    # Fine-tuned (with LoRA adapter)
    python scripts/run_eval.py \
        --model Qwen/Qwen3.5-4B \
        --adapter outputs/stage1_sft/lora_adapter \
        --eval-data data/rarearena_eval_rds.jsonl \
        --max-cases 200 --output outputs/eval_sft_rds_200.json
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import torch

# Ensure packages/ are importable when running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packages" / "models" / "src"))

from rare_archive_models.evaluation.rarearena_eval import (
    EvalCase,
    evaluate_batch,
    save_results,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def load_chat_eval_cases(
    path: Path, max_cases: int | None = None
) -> list[EvalCase]:
    """Load eval JSONL in chat format and convert to EvalCase objects.

    Chat format has a ``messages`` array:
      [0] system prompt
      [1] user message  → clinical_vignette
      [2] assistant msg → ground_truth_diagnosis

    Also supports flat format with ``clinical_vignette`` / ``ground_truth_diagnosis``.
    """
    cases: list[EvalCase] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)

            if "messages" in data:
                msgs = data["messages"]
                vignette = msgs[1]["content"] if len(msgs) > 1 else ""
                diagnosis = msgs[2]["content"] if len(msgs) > 2 else ""
            else:
                vignette = data.get("clinical_vignette", data.get("input", ""))
                diagnosis = data.get("ground_truth_diagnosis", data.get("output", ""))

            cases.append(
                EvalCase(
                    case_id=data.get("case_id", str(len(cases))),
                    clinical_vignette=vignette,
                    ground_truth=diagnosis,
                    disease_id=data.get("disease_id"),
                    patient_category=data.get("patient_category"),
                )
            )
            if max_cases and len(cases) >= max_cases:
                break

    logger.info(f"Loaded {len(cases)} eval cases from {path}")
    return cases


def _get_text_tokenizer(tokenizer):
    """Extract the text tokenizer from a processor (VL models) or return as-is."""
    if hasattr(tokenizer, "tokenizer"):
        # Processor wrapping a tokenizer (e.g., Qwen3VLProcessor)
        return tokenizer.tokenizer
    return tokenizer


def load_model(model_name: str, adapter_path: str | None = None):
    """Load model via Unsloth, optionally merging a LoRA adapter.

    Returns (model, text_tokenizer).
    """
    from unsloth import FastLanguageModel

    logger.info(f"Loading base model: {model_name}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=adapter_path if adapter_path else model_name,
        max_seq_length=4096,
        load_in_4bit=True,
        dtype=torch.bfloat16,
    )

    FastLanguageModel.for_inference(model)
    text_tokenizer = _get_text_tokenizer(tokenizer)
    logger.info(f"Model ready for inference (tokenizer: {type(text_tokenizer).__name__})")
    return model, text_tokenizer


def make_model_fn(model, tokenizer, max_new_tokens: int = 512, temperature: float = 0.3):
    """Create a model_fn(prompt) -> str callable for the eval harness."""

    def model_fn(prompt: str) -> str:
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id,
            )
        # Decode only the new tokens
        new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
        return tokenizer.decode(new_tokens, skip_special_tokens=True)

    return model_fn


def main():
    parser = argparse.ArgumentParser(description="RareArena model evaluation")
    parser.add_argument("--model", required=True, help="HuggingFace model name or local path")
    parser.add_argument("--adapter", default=None, help="Path to LoRA adapter directory")
    parser.add_argument("--eval-data", required=True, help="Path to eval JSONL")
    parser.add_argument("--max-cases", type=int, default=None, help="Limit eval cases")
    parser.add_argument("--output", required=True, help="Path for output JSON")
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--temperature", type=float, default=0.3)
    args = parser.parse_args()

    # Load eval cases
    cases = load_chat_eval_cases(Path(args.eval_data), args.max_cases)
    if not cases:
        logger.error("No eval cases loaded — check data path")
        sys.exit(1)

    # Load model
    model, tokenizer = load_model(args.model, args.adapter)
    model_fn = make_model_fn(model, tokenizer, args.max_new_tokens, args.temperature)

    # Run evaluation
    logger.info(f"Evaluating {len(cases)} cases...")
    t0 = time.time()
    metrics = evaluate_batch(cases, model_fn)
    elapsed = time.time() - t0

    metrics["model"] = args.model
    metrics["adapter"] = args.adapter
    metrics["eval_data"] = args.eval_data
    metrics["elapsed_seconds"] = round(elapsed, 1)

    # Print summary
    print(f"\n{'='*60}")
    print(f"Model:       {args.model}")
    print(f"Adapter:     {args.adapter or 'none (baseline)'}")
    print(f"Cases:       {metrics['n_cases']}")
    print(f"Top-1 acc:   {metrics['top_1_accuracy']:.2%} ({metrics['top_1_count']}/{metrics['n_cases']})")
    print(f"Top-5 acc:   {metrics['top_5_accuracy']:.2%} ({metrics['top_5_count']}/{metrics['n_cases']})")
    print(f"Mean score:  {metrics['mean_score']:.4f}")
    print(f"Time:        {elapsed:.1f}s ({elapsed/max(len(cases),1):.2f}s/case)")
    print(f"{'='*60}\n")

    # Save
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_results(metrics, output_path)


if __name__ == "__main__":
    main()
