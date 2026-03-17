"""Merge LoRA adapter weights into base model.

Step 1 of the quantization pipeline: merge_lora.py -> quantize_gguf.py -> validate_quant.py
"""

import argparse
import logging
from pathlib import Path

import torch

logger = logging.getLogger(__name__)


def merge_lora(
    base_model: str,
    adapter_path: str,
    output_path: str,
    device: str = "auto",
) -> Path:
    """Merge a LoRA adapter into its base model.

    Args:
        base_model: HuggingFace model ID or local path
        adapter_path: Path to the LoRA adapter directory
        output_path: Output directory for the merged model
        device: Device for merging ("auto", "cpu", "cuda")

    Returns:
        Path to the merged model directory
    """
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    output = Path(output_path)
    output.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading base model: {base_model}")
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.bfloat16,
        device_map=device,
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)

    logger.info(f"Loading LoRA adapter: {adapter_path}")
    model = PeftModel.from_pretrained(model, adapter_path)

    logger.info("Merging weights...")
    model = model.merge_and_unload()

    logger.info(f"Saving merged model to {output}")
    model.save_pretrained(output, safe_serialization=True)
    tokenizer.save_pretrained(output)

    logger.info("Merge complete")
    return output


def main():
    parser = argparse.ArgumentParser(description="Merge LoRA adapter into base model")
    parser.add_argument("--base-model", required=True, help="Base model name or path")
    parser.add_argument("--adapter-path", required=True, help="LoRA adapter directory")
    parser.add_argument("--output-path", required=True, help="Output merged model directory")
    parser.add_argument("--device", default="auto", help="Device (auto/cpu/cuda)")
    args = parser.parse_args()

    merge_lora(args.base_model, args.adapter_path, args.output_path, args.device)


if __name__ == "__main__":
    main()
