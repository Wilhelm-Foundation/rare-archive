"""Stage 1: Supervised Fine-Tuning for clinical diagnostic reasoning.

Uses Unsloth for dense models (QLoRA 4-bit) and Swift for MoE (bf16 LoRA).
Trains on RareArena + synthetic patient data.

Usage:
    python -m rare_archive_models.training.stage1_sft --config configs/stages/stage1_sft.yaml
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import torch
import yaml

logger = logging.getLogger(__name__)


@dataclass
class SFTConfig:
    """Configuration for Stage 1 SFT training."""
    # Model
    model_name: str = "Qwen/Qwen3.5-4B"
    model_size: str = "4b"
    architecture: str = "dense"  # dense or moe

    # LoRA
    lora_rank: int = 64
    lora_alpha: int = 128
    lora_dropout: float = 0.05
    target_modules: list[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ])

    # Training
    max_seq_length: int = 4096
    per_device_train_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    num_train_epochs: int = 3
    learning_rate: float = 2e-4
    warmup_ratio: float = 0.1
    weight_decay: float = 0.01
    lr_scheduler_type: str = "cosine"
    bf16: bool = True
    gradient_checkpointing: bool = True

    # Data
    train_data: str = ""
    eval_data: str = ""
    max_samples: int | None = None

    # Quantization (for Unsloth)
    load_in_4bit: bool = True
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_compute_dtype: str = "bfloat16"

    # Logging
    report_to: str = "tensorboard"

    # Output
    output_dir: str = "outputs/stage1_sft"
    hub_model_id: str = ""
    patient_category: str = "general"

    @classmethod
    def from_yaml(cls, path: Path) -> "SFTConfig":
        """Load config from YAML file, supporting hierarchical overlay."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def from_hierarchy(
        cls,
        base_path: Path,
        stage_path: Path,
        category_path: Path | None = None,
    ) -> "SFTConfig":
        """Load config from hierarchical YAML overlay:
        base/{size}.yaml -> stages/{stage}/ -> categories/{category}.yaml
        """
        config = {}
        for path in [base_path, stage_path]:
            if path.exists():
                with open(path) as f:
                    data = yaml.safe_load(f) or {}
                config.update(data)

        if category_path and category_path.exists():
            with open(category_path) as f:
                data = yaml.safe_load(f) or {}
            config.update(data)

        # Coerce values to match dataclass field types (PyYAML 1.1 mis-parses e.g. 2e-4 as str)
        coerced = {}
        for k, v in config.items():
            if k not in cls.__dataclass_fields__:
                continue
            expected = cls.__dataclass_fields__[k].type
            if expected is float and isinstance(v, str):
                v = float(v)
            elif expected is int and isinstance(v, str):
                v = int(v)
            coerced[k] = v
        return cls(**coerced)


def load_training_data(
    data_path: str,
    max_samples: int | None = None,
) -> list[dict[str, Any]]:
    """Load training data from JSONL (chat format)."""
    records = []
    path = Path(data_path)

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            records.append(record)
            if max_samples and len(records) >= max_samples:
                break

    logger.info(f"Loaded {len(records)} training examples from {path}")
    return records


def format_chat_template(
    messages: list[dict[str, str]],
    tokenizer: Any,
) -> str:
    """Format messages using the model's chat template."""
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
    )


def train_unsloth(config: SFTConfig) -> Path:
    """Train a dense model using Unsloth QLoRA.

    Returns path to the saved LoRA adapter.
    """
    from unsloth import FastLanguageModel
    from trl import SFTTrainer, SFTConfig as TRLSFTConfig

    logger.info(f"Loading model: {config.model_name}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=config.model_name,
        max_seq_length=config.max_seq_length,
        load_in_4bit=config.load_in_4bit,
        dtype=torch.bfloat16 if config.bf16 else torch.float16,
    )
    # Extract text tokenizer from processor (VL models like Qwen3.5)
    if hasattr(tokenizer, "tokenizer"):
        tokenizer = tokenizer.tokenizer

    logger.info(f"Applying LoRA: rank={config.lora_rank}, alpha={config.lora_alpha}")
    model = FastLanguageModel.get_peft_model(
        model,
        r=config.lora_rank,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        target_modules=config.target_modules,
        bias="none",
        use_gradient_checkpointing="unsloth",
    )

    # Load and format data
    train_data = load_training_data(config.train_data, config.max_samples)

    def format_example(example: dict) -> dict:
        messages = example.get("messages", [])
        text = format_chat_template(messages, tokenizer)
        return {"text": text}

    from datasets import Dataset
    train_dataset = Dataset.from_list(train_data).map(format_example)

    eval_dataset = None
    if config.eval_data:
        eval_data = load_training_data(config.eval_data)
        eval_dataset = Dataset.from_list(eval_data).map(format_example)

    # Configure trainer
    training_args = TRLSFTConfig(
        output_dir=config.output_dir,
        per_device_train_batch_size=config.per_device_train_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        num_train_epochs=config.num_train_epochs,
        learning_rate=config.learning_rate,
        warmup_ratio=config.warmup_ratio,
        weight_decay=config.weight_decay,
        lr_scheduler_type=config.lr_scheduler_type,
        bf16=config.bf16,
        logging_steps=10,
        save_strategy="epoch",
        eval_strategy="epoch" if eval_dataset else "no",
        max_seq_length=config.max_seq_length,
        dataset_text_field="text",
        report_to=config.report_to,
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        args=training_args,
    )

    logger.info("Starting training...")
    trainer.train()

    # Save LoRA adapter
    adapter_path = Path(config.output_dir) / "lora_adapter"
    model.save_pretrained(adapter_path)
    tokenizer.save_pretrained(adapter_path)
    logger.info(f"LoRA adapter saved to {adapter_path}")

    return adapter_path


def train_swift_moe(config: SFTConfig) -> Path:
    """Train a MoE model using Swift bf16 LoRA.

    Returns path to the saved LoRA adapter.
    """
    import subprocess

    swift_args = [
        "swift", "sft",
        "--model", config.model_name,
        "--dataset", config.train_data,
        "--output_dir", config.output_dir,
        "--lora_rank", str(config.lora_rank),
        "--lora_alpha", str(config.lora_alpha),
        "--lora_dropout", str(config.lora_dropout),
        "--target_modules", ",".join(config.target_modules),
        "--max_length", str(config.max_seq_length),
        "--per_device_train_batch_size", str(config.per_device_train_batch_size),
        "--gradient_accumulation_steps", str(config.gradient_accumulation_steps),
        "--num_train_epochs", str(config.num_train_epochs),
        "--learning_rate", str(config.learning_rate),
        "--warmup_ratio", str(config.warmup_ratio),
        "--bf16", "true",
        "--gradient_checkpointing", "true",
    ]

    logger.info(f"Running Swift SFT: {' '.join(swift_args)}")
    result = subprocess.run(swift_args, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Swift SFT failed:\n{result.stderr}")

    adapter_path = Path(config.output_dir) / "lora_adapter"
    logger.info(f"Swift LoRA adapter saved to {adapter_path}")
    return adapter_path


def train(config: SFTConfig) -> Path:
    """Train using the appropriate framework based on architecture."""
    if config.architecture == "moe":
        return train_swift_moe(config)
    else:
        return train_unsloth(config)


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Stage 1 SFT Training")
    parser.add_argument("--config", required=True, help="Path to config YAML")
    parser.add_argument("--base-config", help="Base size config")
    parser.add_argument("--category-config", help="Category overlay config")
    args = parser.parse_args()

    if args.base_config:
        config = SFTConfig.from_hierarchy(
            Path(args.base_config),
            Path(args.config),
            Path(args.category_config) if args.category_config else None,
        )
    else:
        config = SFTConfig.from_yaml(Path(args.config))

    adapter_path = train(config)
    print(f"Training complete. Adapter: {adapter_path}")


if __name__ == "__main__":
    main()
