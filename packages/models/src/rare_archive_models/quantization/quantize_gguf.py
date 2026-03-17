"""Convert merged model to GGUF format using llama.cpp.

Step 2 of the quantization pipeline: merge_lora.py -> quantize_gguf.py -> validate_quant.py
"""

import argparse
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Quantization methods ordered by quality (highest to lowest)
QUANT_METHODS = {
    "F16": {"bits": 16, "description": "Full 16-bit, no quantization"},
    "Q8_0": {"bits": 8, "description": "8-bit, best quality quantized"},
    "Q6_K": {"bits": 6, "description": "6-bit K-quant, very high quality"},
    "Q5_K_M": {"bits": 5, "description": "5-bit K-quant medium, good quality"},
    "Q4_K_M": {"bits": 4, "description": "4-bit K-quant medium, standard"},
}

# Tier-appropriate quantization defaults
TIER_DEFAULTS = {
    "L1": "Q4_K_M",
    "L2": "Q8_0",
    "L3": "F16",
}


def convert_to_gguf(
    model_path: str,
    output_path: str,
    llama_cpp_path: str = "llama.cpp",
    outtype: str = "f16",
) -> Path:
    """Convert a HuggingFace model to GGUF format.

    Args:
        model_path: Path to the merged HuggingFace model
        output_path: Output GGUF file path
        llama_cpp_path: Path to llama.cpp repository
        outtype: Output type for conversion (f16, f32, bf16)

    Returns:
        Path to the GGUF file
    """
    convert_script = Path(llama_cpp_path) / "convert_hf_to_gguf.py"
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "python", str(convert_script),
        model_path,
        "--outfile", str(output),
        "--outtype", outtype,
    ]

    logger.info(f"Converting to GGUF: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"GGUF conversion failed:\n{result.stderr}")

    logger.info(f"GGUF file created: {output} ({output.stat().st_size / 1e9:.2f} GB)")
    return output


def quantize_gguf(
    input_gguf: str,
    output_gguf: str,
    method: str = "Q5_K_M",
    llama_cpp_path: str = "llama.cpp",
) -> Path:
    """Quantize a GGUF file.

    Args:
        input_gguf: Path to the F16 GGUF file
        output_gguf: Output quantized GGUF file path
        method: Quantization method (Q4_K_M, Q5_K_M, Q6_K, Q8_0)
        llama_cpp_path: Path to llama.cpp build directory

    Returns:
        Path to the quantized GGUF file
    """
    quantize_bin = Path(llama_cpp_path) / "build" / "bin" / "llama-quantize"
    output = Path(output_gguf)
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [str(quantize_bin), input_gguf, str(output), method]

    logger.info(f"Quantizing: {method}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Quantization failed:\n{result.stderr}")

    logger.info(f"Quantized GGUF: {output} ({output.stat().st_size / 1e9:.2f} GB)")
    return output


def main():
    parser = argparse.ArgumentParser(description="Convert and quantize model to GGUF")
    parser.add_argument("--model-path", required=True, help="Merged HF model path")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--method", default="Q5_K_M", choices=list(QUANT_METHODS.keys()))
    parser.add_argument("--llama-cpp-path", default="llama.cpp", help="llama.cpp repo path")
    parser.add_argument("--model-name", required=True, help="Model name for output file")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Convert to F16 GGUF
    f16_path = output_dir / f"{args.model_name}-f16.gguf"
    convert_to_gguf(args.model_path, str(f16_path), args.llama_cpp_path)

    # Step 2: Quantize
    if args.method != "F16":
        quant_path = output_dir / f"{args.model_name}-{args.method}.gguf"
        quantize_gguf(str(f16_path), str(quant_path), args.method, args.llama_cpp_path)
        print(f"Quantized model: {quant_path}")
    else:
        print(f"F16 model: {f16_path}")


if __name__ == "__main__":
    main()
