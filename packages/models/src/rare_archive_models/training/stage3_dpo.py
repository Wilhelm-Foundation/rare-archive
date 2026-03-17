"""Stage 3: DPO/GRPO — Clinician preference alignment.

Uses preference pairs from the RLHF portal (L2 expert evaluations).
Framework: Swift for both MoE and dense (DPO/GRPO native support).

Usage:
    python -m rare_archive_models.training.stage3_dpo --config configs/stages/stage3_dpo.yaml
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class DPOConfig:
    """Configuration for Stage 3 DPO/GRPO training."""
    model_name: str = "Qwen/Qwen3.5-4B"
    adapter_path: str = ""  # Stage 2 adapter
    architecture: str = "dense"
    method: str = "dpo"  # dpo or grpo

    # LoRA
    lora_rank: int = 32
    lora_alpha: int = 64
    target_modules: list[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
    ])

    # DPO-specific
    beta: float = 0.1  # KL penalty coefficient
    loss_type: str = "sigmoid"  # sigmoid, hinge, ipo

    # GRPO-specific
    reward_model: str = ""  # Path to reward model or "rarearena" for eval-based reward
    num_generations: int = 4  # Generations per prompt for GRPO
    kl_coeff: float = 0.05

    # Training
    max_seq_length: int = 4096
    per_device_train_batch_size: int = 2
    gradient_accumulation_steps: int = 8
    num_train_epochs: int = 1
    learning_rate: float = 5e-5
    warmup_ratio: float = 0.1
    bf16: bool = True

    # Data
    train_data: str = "data/rlhf_preferences.jsonl"
    eval_data: str = ""

    # Output
    output_dir: str = "outputs/stage3_dpo"
    patient_category: str = "general"

    @classmethod
    def from_yaml(cls, path: Path) -> "DPOConfig":
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def load_preference_pairs(path: Path) -> list[dict[str, Any]]:
    """Load DPO-compatible preference pairs.

    Expected format:
    {
        "prompt": "clinical vignette...",
        "chosen": "preferred response...",
        "rejected": "rejected response...",
        "metadata": {
            "expert_id": "...",
            "patient_category": "...",
            "annotations": {...}
        }
    }
    """
    pairs = []
    with open(path) as f:
        for line in f:
            if line.strip():
                pairs.append(json.loads(line))
    logger.info(f"Loaded {len(pairs)} preference pairs from {path}")
    return pairs


def train_dpo_swift(config: DPOConfig) -> Path:
    """Train DPO using Swift framework."""
    import subprocess

    cmd = [
        "swift", "rlhf",
        "--rlhf_type", config.method,
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
        "--beta", str(config.beta),
        "--loss_type", config.loss_type,
    ]

    if config.adapter_path:
        cmd.extend(["--adapters", config.adapter_path])

    logger.info(f"Running Swift {config.method.upper()}: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Swift {config.method.upper()} failed:\n{result.stderr}")

    adapter_path = Path(config.output_dir) / "lora_adapter"
    logger.info(f"Adapter saved to {adapter_path}")
    return adapter_path


def train_dpo_trl(config: DPOConfig) -> Path:
    """Train DPO using TRL library (for dense models)."""
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import DPOConfig as TRLDPOConfig, DPOTrainer
    import torch

    logger.info(f"Loading model: {config.model_name}")
    model = AutoModelForCausalLM.from_pretrained(
        config.model_name,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(config.model_name, trust_remote_code=True)

    if not tokenizer.pad_token:
        tokenizer.pad_token = tokenizer.eos_token

    # Load preference pairs
    pairs = load_preference_pairs(Path(config.train_data))
    dataset = Dataset.from_list(pairs)

    peft_config = LoraConfig(
        r=config.lora_rank,
        lora_alpha=config.lora_alpha,
        target_modules=config.target_modules,
        bias="none",
        task_type="CAUSAL_LM",
    )

    training_args = TRLDPOConfig(
        output_dir=config.output_dir,
        per_device_train_batch_size=config.per_device_train_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        num_train_epochs=config.num_train_epochs,
        learning_rate=config.learning_rate,
        warmup_ratio=config.warmup_ratio,
        bf16=config.bf16,
        beta=config.beta,
        loss_type=config.loss_type,
        logging_steps=10,
        save_strategy="epoch",
        max_length=config.max_seq_length,
    )

    trainer = DPOTrainer(
        model=model,
        ref_model=None,  # Uses implicit reference model
        args=training_args,
        train_dataset=dataset,
        tokenizer=tokenizer,
        peft_config=peft_config,
    )

    trainer.train()

    adapter_path = Path(config.output_dir) / "lora_adapter"
    trainer.save_model(adapter_path)
    tokenizer.save_pretrained(adapter_path)
    return adapter_path


def train(config: DPOConfig) -> Path:
    """Route to appropriate DPO/GRPO trainer."""
    if config.architecture == "moe" or config.method == "grpo":
        return train_dpo_swift(config)
    return train_dpo_trl(config)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Stage 3 DPO/GRPO")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = DPOConfig.from_yaml(Path(args.config))
    train(config)
