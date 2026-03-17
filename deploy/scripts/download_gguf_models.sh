#!/usr/bin/env bash
# Rare AI Archive — GGUF Model Downloader
# Downloads models from HuggingFace with checksum verification
#
# Usage:
#   ./download_gguf_models.sh [--catalog catalog.json] [--output-dir /data/models]
#   ./download_gguf_models.sh --model qwen3.5-35b-a3b-q8_0

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CATALOG="${SCRIPT_DIR}/../catalog/catalog.json"
OUTPUT_DIR="/data/latlab/rare-archive/models"
HF_ORG="wilhelm-foundation"
SPECIFIC_MODEL=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --catalog) CATALOG="$2"; shift 2 ;;
        --output-dir) OUTPUT_DIR="$2"; shift 2 ;;
        --model) SPECIFIC_MODEL="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

echo "╔══════════════════════════════════════════╗"
echo "║   Rare AI Archive — Model Downloader     ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Catalog: ${CATALOG}"
echo "Output:  ${OUTPUT_DIR}"
echo ""

mkdir -p "${OUTPUT_DIR}"

if [ ! -f "${CATALOG}" ]; then
    echo "ERROR: Catalog not found: ${CATALOG}"
    exit 1
fi

# Parse catalog and download models
python3 -c "
import json, sys, subprocess, hashlib
from pathlib import Path

catalog_path = '${CATALOG}'
output_dir = Path('${OUTPUT_DIR}')
specific = '${SPECIFIC_MODEL}'

with open(catalog_path) as f:
    catalog = json.load(f)

for model in catalog.get('models', []):
    name = model['name']
    if specific and specific != name:
        continue

    filename = model['filename']
    output_path = output_dir / filename
    sha256 = model.get('sha256', '')
    hf_repo = model.get('hf_repo', '')
    hf_file = model.get('hf_file', filename)

    # Check if already downloaded and verified
    if output_path.exists() and sha256:
        h = hashlib.sha256()
        with open(output_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        if h.hexdigest() == sha256:
            print(f'  [skip] {name} — already downloaded and verified')
            continue
        else:
            print(f'  [warn] {name} — checksum mismatch, re-downloading')

    # Download
    print(f'  [download] {name} from {hf_repo}')
    if hf_repo:
        cmd = ['huggingface-cli', 'download', hf_repo, hf_file,
               '--local-dir', str(output_dir), '--local-dir-use-symlinks', 'False']
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f'  [error] Failed to download {name}: {result.stderr}')
            continue

    # Verify checksum
    if sha256 and output_path.exists():
        h = hashlib.sha256()
        with open(output_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        if h.hexdigest() == sha256:
            print(f'  [ok] {name} — verified')
        else:
            print(f'  [FAIL] {name} — checksum verification failed')
            sys.exit(1)
    else:
        print(f'  [ok] {name} — downloaded (no checksum to verify)')
"

echo ""
echo "Models ready in ${OUTPUT_DIR}:"
ls -lh "${OUTPUT_DIR}"/*.gguf 2>/dev/null || echo "  (no GGUF files found)"
