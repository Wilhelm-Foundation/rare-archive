# L1 Local Setup — Rare AI Archive

Run the 4B rare disease SFT model locally on any Apple Silicon Mac with Metal acceleration.

## Requirements

- macOS with Apple Silicon (M1/M2/M3/M4)
- 8 GB+ RAM (model uses ~4.2 GB)
- Xcode Command Line Tools: `xcode-select --install`
- cmake: `brew install cmake`
- Python 3.11 or 3.12 (OpenWebUI requires <3.13)

## Step 1: Build llama.cpp

```bash
cd ~/Projects
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
cmake -B build -DGGML_METAL=ON
cmake --build build --config Release -j$(sysctl -n hw.ncpu)
```

Verify:
```bash
./build/bin/llama-server --version
# Should show "ggml_metal_device_init: GPU name: ..."
```

## Step 2: Download the Model

### Option A: Q8_0 from HuggingFace (recommended — max quality)

```bash
mkdir -p ~/Models
pip install huggingface_hub
huggingface-cli download Wilhelm-Foundation/rare-archive-qwen-4b-sft-v1 \
  rare-archive-qwen-4b-sft-v1-Q8_0.gguf \
  --local-dir ~/Models
```

### Option A2: Q5_K_M (smaller — good tradeoff for 8-16 GB Macs)

```bash
mkdir -p ~/Models
huggingface-cli download Wilhelm-Foundation/rare-archive-qwen-4b-sft-v1 \
  rare-archive-qwen-4b-sft-v1-Q5_K_M.gguf \
  --local-dir ~/Models
```

Q5_K_M is ~2.8 GB vs Q8_0's 4.2 GB, with minimal quality loss. See [quantization guide](quantization_guide.md) for full comparison.

### Option B: From L2 (internal)

```bash
mkdir -p ~/Models
scp latlab-dell:/data/latlab/rare-archive/models/rare-archive-qwen-4b-sft-v1-Q8_0.gguf ~/Models/
```

## Step 3: Start llama-server

```bash
~/Projects/llama.cpp/build/bin/llama-server \
  -m ~/Models/rare-archive-qwen-4b-sft-v1-Q8_0.gguf \
  -ngl 99 --port 8082
```

Verify:
```bash
curl http://localhost:8082/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "rare-archive",
    "messages": [{"role": "user", "content": "What is Gaucher disease?"}],
    "max_tokens": 100
  }'
```

Expected: structured clinical response about glucocerebrosidase deficiency.

## Step 4: Install OpenWebUI (optional)

OpenWebUI provides a browser-based chat interface.

```bash
# Requires Python 3.11 or 3.12
python3.12 -m venv ~/Projects/rare-archive-ui
source ~/Projects/rare-archive-ui/bin/activate
pip install open-webui
```

Start with the local model:
```bash
source ~/Projects/rare-archive-ui/bin/activate
OPENAI_API_BASE_URLS="http://localhost:8082/v1" \
  open-webui serve --port 3100
```

Open http://localhost:3100 in your browser. Create an admin account on first visit.

## Performance Notes

| Mac | RAM | Tokens/sec (est.) | Notes |
|-----|-----|-------------------|-------|
| M4 Max | 128 GB | ~80-120 t/s | Full GPU offload, 96 GB headroom |
| M3 Pro | 36 GB | ~40-60 t/s | Full GPU offload |
| M1 | 16 GB | ~20-30 t/s | Full GPU offload, tight on RAM |
| M1 | 8 GB | ~15-20 t/s | May need `-ngl 20` for partial offload |

The Q8_0 model is 4.2 GB. Any Mac with 8+ GB RAM can run it with full Metal offload (`-ngl 99`).

## Troubleshooting

**cmake not found**: `brew install cmake`

**Python version error with OpenWebUI**: OpenWebUI requires Python <3.13. Use `python3.12` or `python3.11`. Check with `python3 --version`.

**Port 8082 already in use**: Change to another port: `--port 8083`

**Slow generation**: Ensure Metal is enabled (check for `ggml_metal_device_init` in startup output). If missing, rebuild with `-DGGML_METAL=ON`.

## Model Details

| Property | Value |
|----------|-------|
| Base model | Qwen/Qwen3.5-4B |
| Fine-tuning | QLoRA SFT, 63K examples, 3 epochs |
| Quantization | Q8_0 (4.2 GB) |
| Top-1 accuracy | 21.5% (21.5x over base) |
| License | Apache-2.0 |
| HuggingFace | [Wilhelm-Foundation/rare-archive-qwen-4b-sft-v1](https://huggingface.co/Wilhelm-Foundation/rare-archive-qwen-4b-sft-v1) |

## Persistent Serving (systemd)

To keep llama-server running across reboots on a Linux L1 node:

```bash
# /etc/systemd/system/rare-archive-llama.service
[Unit]
Description=Rare Archive llama-server
After=network.target

[Service]
Type=simple
User=latlab
ExecStart=/usr/local/bin/llama-server \
  -m /data/models/rare-archive-qwen-4b-sft-v1-Q8_0.gguf \
  -ngl 99 --port 8082
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now rare-archive-llama
```

For macOS, use a LaunchAgent plist instead (or just run in a tmux session).
