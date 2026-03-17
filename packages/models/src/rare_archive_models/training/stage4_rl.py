"""Stage 4: Progressive RL — RareArena-derived reward optimization.

Three-phase progressive training (inspired by Med-R3):
1. Reasoner phase: Optimize clinical reasoning quality
2. Retriever phase: Optimize tool retrieval effectiveness
3. Collaboration phase: Joint optimization of reasoning + retrieval

Reward function derived from RareArena evaluation:
- Top-1 accuracy contributes to base reward
- Tool usage quality adds bonus reward
- Safety violations incur penalty

Usage:
    python -m rare_archive_models.training.stage4_rl --config configs/stages/stage4_rl.yaml
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml

logger = logging.getLogger(__name__)


@dataclass
class RLConfig:
    """Configuration for Stage 4 Progressive RL."""
    model_name: str = "Qwen/Qwen3.5-4B"
    adapter_path: str = ""  # Stage 3 adapter
    architecture: str = "dense"

    # RL method
    method: str = "grpo"  # grpo or ppo
    phase: str = "reasoner"  # reasoner, retriever, collaboration

    # LoRA
    lora_rank: int = 32
    lora_alpha: int = 64
    target_modules: list[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
    ])

    # RL-specific
    num_generations: int = 4
    kl_coeff: float = 0.05
    reward_baseline: str = "mean"  # mean, median, none
    clip_range: float = 0.2
    max_grad_norm: float = 1.0

    # Reward function
    reward_weights: dict[str, float] = field(default_factory=lambda: {
        "diagnostic_accuracy": 1.0,
        "reasoning_quality": 0.3,
        "tool_usage": 0.2,
        "safety": 0.5,
    })

    # Training
    max_seq_length: int = 8192
    per_device_train_batch_size: int = 1
    gradient_accumulation_steps: int = 16
    num_train_epochs: int = 1
    learning_rate: float = 1e-5
    bf16: bool = True

    # Data
    train_data: str = "data/rarearena_rds_train.jsonl"
    eval_data: str = "data/rarearena_rds_eval.jsonl"

    # Output
    output_dir: str = "outputs/stage4_rl"

    @classmethod
    def from_yaml(cls, path: Path) -> "RLConfig":
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def compute_reward(
    response: str,
    ground_truth: str,
    weights: dict[str, float],
    phase: str = "reasoner",
) -> float:
    """Compute reward for a model response.

    Reward components:
    - diagnostic_accuracy: Does the response mention the correct diagnosis? (0, 1, 2)
    - reasoning_quality: Is the reasoning chain coherent? (heuristic)
    - tool_usage: Are tools used appropriately? (for retriever/collaboration phases)
    - safety: No dangerous recommendations? (penalty for violations)
    """
    reward = 0.0

    # Diagnostic accuracy (simplified — full version uses GPT-4o scoring)
    response_lower = response.lower()
    truth_lower = ground_truth.lower()

    if truth_lower in response_lower:
        accuracy_score = 2.0
    elif any(word in response_lower for word in truth_lower.split() if len(word) > 3):
        accuracy_score = 1.0
    else:
        accuracy_score = 0.0

    reward += weights.get("diagnostic_accuracy", 1.0) * accuracy_score

    # Reasoning quality (heuristic: longer, structured responses score higher)
    has_reasoning = any(marker in response_lower for marker in [
        "because", "suggests", "consistent with", "differential",
        "based on", "evidence", "considering",
    ])
    reasoning_score = 1.0 if has_reasoning else 0.0
    reward += weights.get("reasoning_quality", 0.3) * reasoning_score

    # Tool usage (only in retriever and collaboration phases)
    if phase in ("retriever", "collaboration"):
        has_tool_calls = "tool_calls" in response_lower or "function" in response_lower
        tool_score = 1.0 if has_tool_calls else 0.0
        reward += weights.get("tool_usage", 0.2) * tool_score

    # Safety penalty
    safety_violations = [
        "stop taking medication",
        "do not see a doctor",
        "definitely has",
        "i am certain this is",
    ]
    has_violation = any(v in response_lower for v in safety_violations)
    if has_violation:
        reward -= weights.get("safety", 0.5) * 2.0

    return reward


def train_progressive_rl(config: RLConfig) -> Path:
    """Run progressive RL training via Swift GRPO."""
    import subprocess

    cmd = [
        "swift", "rlhf",
        "--rlhf_type", "grpo",
        "--model", config.model_name,
        "--dataset", config.train_data,
        "--output_dir", config.output_dir,
        "--lora_rank", str(config.lora_rank),
        "--lora_alpha", str(config.lora_alpha),
        "--target_modules", ",".join(config.target_modules),
        "--max_length", str(config.max_seq_length),
        "--per_device_train_batch_size", str(config.per_device_train_batch_size),
        "--gradient_accumulation_steps", str(config.gradient_accumulation_steps),
        "--num_train_epochs", str(config.num_train_epochs),
        "--learning_rate", str(config.learning_rate),
        "--bf16", "true",
        "--num_generations", str(config.num_generations),
        "--kl_coeff", str(config.kl_coeff),
    ]

    if config.adapter_path:
        cmd.extend(["--adapters", config.adapter_path])

    logger.info(f"Running Progressive RL ({config.phase} phase)")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Progressive RL failed:\n{result.stderr}")

    adapter_path = Path(config.output_dir) / "lora_adapter"
    return adapter_path


def run_full_progressive(
    base_config: RLConfig,
    phases: list[str] | None = None,
) -> dict[str, Path]:
    """Run the full 3-phase progressive RL pipeline.

    Phase 1 (Reasoner): Optimize diagnostic reasoning without tools
    Phase 2 (Retriever): Optimize tool retrieval and usage
    Phase 3 (Collaboration): Joint optimization
    """
    if phases is None:
        phases = ["reasoner", "retriever", "collaboration"]

    results = {}
    current_adapter = base_config.adapter_path

    for phase in phases:
        logger.info(f"Starting phase: {phase}")
        config = RLConfig(
            model_name=base_config.model_name,
            adapter_path=current_adapter,
            architecture=base_config.architecture,
            phase=phase,
            train_data=base_config.train_data,
            eval_data=base_config.eval_data,
            output_dir=f"{base_config.output_dir}/{phase}",
            reward_weights=base_config.reward_weights,
            lora_rank=base_config.lora_rank,
            lora_alpha=base_config.lora_alpha,
            target_modules=base_config.target_modules,
        )

        adapter_path = train_progressive_rl(config)
        results[phase] = adapter_path
        current_adapter = str(adapter_path)
        logger.info(f"Phase {phase} complete: {adapter_path}")

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Stage 4 Progressive RL")
    parser.add_argument("--config", required=True)
    parser.add_argument("--phase", choices=["reasoner", "retriever", "collaboration", "all"], default="all")
    args = parser.parse_args()

    config = RLConfig.from_yaml(Path(args.config))

    if args.phase == "all":
        run_full_progressive(config)
    else:
        config.phase = args.phase
        train_progressive_rl(config)
