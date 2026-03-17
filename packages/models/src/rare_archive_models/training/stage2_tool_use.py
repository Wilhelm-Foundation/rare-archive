"""Stage 2: Tool-Use SFT — Agentic diagnostic tool invocation.

Trains the model to use clinical tools (ClinVar, Orphanet, PanelApp, gnomAD,
HPO, PubMed) via structured function-calling traces.

Tool actions follow the Reason/Lookup/Match/Search/Diagnose pattern:
1. Reason: Analyze clinical presentation, identify key features
2. Lookup: Query specific databases for information
3. Match: Cross-reference findings across sources
4. Search: Broaden search when initial results are insufficient
5. Diagnose: Synthesize findings into ranked differential

Usage:
    python -m rare_archive_models.training.stage2_tool_use --config configs/stages/stage2_tool_use.yaml
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "clinvar_lookup",
            "description": "Look up variant pathogenicity in ClinVar",
            "parameters": {
                "type": "object",
                "properties": {
                    "variant": {"type": "string", "description": "Variant (e.g., 'NM_000546.6:c.215C>G')"},
                    "gene": {"type": "string", "description": "Gene symbol (optional)"},
                },
                "required": ["variant"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "orphanet_search",
            "description": "Search Orphanet for rare disease information",
            "parameters": {
                "type": "object",
                "properties": {
                    "disease_name": {"type": "string", "description": "Disease name to search"},
                },
                "required": ["disease_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "hpo_lookup",
            "description": "Resolve phenotypes to HPO terms",
            "parameters": {
                "type": "object",
                "properties": {
                    "phenotype": {"type": "string", "description": "Clinical phenotype description"},
                },
                "required": ["phenotype"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "panelapp_search",
            "description": "Query gene panels from Genomics England PanelApp",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Disease or gene to search"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "gnomad_lookup",
            "description": "Look up population allele frequencies in gnomAD",
            "parameters": {
                "type": "object",
                "properties": {
                    "variant_id": {"type": "string", "description": "Variant in chrom-pos-ref-alt format"},
                },
                "required": ["variant_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pubmed_search",
            "description": "Search PubMed for medical literature",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "differential_diagnosis",
            "description": "Generate ranked differential diagnosis from symptoms",
            "parameters": {
                "type": "object",
                "properties": {
                    "symptoms": {"type": "string", "description": "Comma-separated symptoms"},
                    "age": {"type": "string"},
                    "sex": {"type": "string"},
                },
                "required": ["symptoms"],
            },
        },
    },
]


@dataclass
class ToolUseSFTConfig:
    """Configuration for Stage 2 Tool-Use SFT."""
    model_name: str = "Qwen/Qwen3.5-4B"
    adapter_path: str = ""  # Stage 1 LoRA adapter to continue from
    architecture: str = "dense"

    # LoRA (continue from Stage 1)
    lora_rank: int = 64
    lora_alpha: int = 128
    target_modules: list[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ])

    # Training
    max_seq_length: int = 8192  # Longer for tool traces
    per_device_train_batch_size: int = 2
    gradient_accumulation_steps: int = 8
    num_train_epochs: int = 2
    learning_rate: float = 1e-4  # Lower LR for stage 2
    warmup_ratio: float = 0.05
    bf16: bool = True

    # Data
    train_data: str = "data/tool_use_traces.jsonl"
    eval_data: str = ""

    # Output
    output_dir: str = "outputs/stage2_tool_use"

    @classmethod
    def from_yaml(cls, path: Path) -> "ToolUseSFTConfig":
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def generate_tool_trace(
    case: dict[str, Any],
    tool_responses: dict[str, Any],
) -> list[dict[str, str]]:
    """Generate a gold-standard agentic diagnostic trace.

    Creates a multi-turn conversation showing ideal tool usage:
    user message -> model reasons -> tool call -> tool result -> model synthesizes

    Args:
        case: Clinical case with vignette and diagnosis
        tool_responses: Pre-computed tool API responses for this case

    Returns:
        List of message dicts in chat format with tool calls
    """
    vignette = case.get("clinical_vignette", "")
    diagnosis = case.get("ground_truth_diagnosis", "")

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert rare disease diagnostician with access to "
                "clinical databases. Use your tools systematically to investigate "
                "the clinical presentation and arrive at a diagnosis."
            ),
        },
        {"role": "user", "content": vignette},
    ]

    # Step 1: Initial reasoning
    messages.append({
        "role": "assistant",
        "content": (
            "Let me analyze this clinical presentation systematically.\n\n"
            "I'll start by identifying the key phenotypic features and querying "
            "relevant databases."
        ),
    })

    # Step 2: HPO lookup for key symptoms
    if "hpo" in tool_responses:
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": "call_hpo",
                "type": "function",
                "function": {
                    "name": "hpo_lookup",
                    "arguments": json.dumps({"phenotype": tool_responses["hpo"]["query"]}),
                },
            }],
        })
        messages.append({
            "role": "tool",
            "tool_call_id": "call_hpo",
            "content": json.dumps(tool_responses["hpo"]["result"]),
        })

    # Step 3: Disease database lookup
    if "orphanet" in tool_responses:
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": "call_orphanet",
                "type": "function",
                "function": {
                    "name": "orphanet_search",
                    "arguments": json.dumps({"disease_name": tool_responses["orphanet"]["query"]}),
                },
            }],
        })
        messages.append({
            "role": "tool",
            "tool_call_id": "call_orphanet",
            "content": json.dumps(tool_responses["orphanet"]["result"]),
        })

    # Step 4: Final synthesis
    messages.append({
        "role": "assistant",
        "content": (
            f"Based on my analysis of the clinical features and database results, "
            f"my primary diagnosis is **{diagnosis}**."
        ),
    })

    return messages


def train(config: ToolUseSFTConfig) -> Path:
    """Train Stage 2 Tool-Use SFT."""
    from unsloth import FastLanguageModel
    from trl import SFTTrainer, SFTConfig as TRLSFTConfig
    from datasets import Dataset
    import torch

    logger.info(f"Loading model: {config.model_name}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=config.model_name,
        max_seq_length=config.max_seq_length,
        load_in_4bit=True,
        dtype=torch.bfloat16,
    )

    # Load Stage 1 adapter if provided
    if config.adapter_path:
        from peft import PeftModel
        logger.info(f"Loading Stage 1 adapter: {config.adapter_path}")
        model = PeftModel.from_pretrained(model, config.adapter_path)
        model = model.merge_and_unload()

    model = FastLanguageModel.get_peft_model(
        model,
        r=config.lora_rank,
        lora_alpha=config.lora_alpha,
        target_modules=config.target_modules,
        bias="none",
        use_gradient_checkpointing="unsloth",
    )

    # Load training data
    train_records = []
    with open(config.train_data) as f:
        for line in f:
            if line.strip():
                train_records.append(json.loads(line))

    def format_example(example):
        messages = example.get("messages", [])
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        return {"text": text}

    train_dataset = Dataset.from_list(train_records).map(format_example)

    training_args = TRLSFTConfig(
        output_dir=config.output_dir,
        per_device_train_batch_size=config.per_device_train_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        num_train_epochs=config.num_train_epochs,
        learning_rate=config.learning_rate,
        warmup_ratio=config.warmup_ratio,
        bf16=config.bf16,
        logging_steps=10,
        save_strategy="epoch",
        max_seq_length=config.max_seq_length,
        dataset_text_field="text",
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        args=training_args,
    )

    trainer.train()

    adapter_path = Path(config.output_dir) / "lora_adapter"
    model.save_pretrained(adapter_path)
    tokenizer.save_pretrained(adapter_path)
    return adapter_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Stage 2 Tool-Use SFT")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = ToolUseSFTConfig.from_yaml(Path(args.config))
    train(config)
