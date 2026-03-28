"""Rare Archive Diagnosis Leaderboard

Open benchmarks for rare disease diagnostic AI.
A program of the Wilhelm Foundation, built with the Lattice Protocol.
"""

import json
from pathlib import Path

import gradio as gr
import pandas as pd

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

RESULTS_PATH = Path(__file__).parent / "results.json"


def load_results() -> pd.DataFrame:
    """Load leaderboard results from results.json."""
    data = json.loads(RESULTS_PATH.read_text())
    rows = []
    for r in data["results"]:
        model_name = r["model"]
        if r.get("model_url"):
            model_name = f"[{r['model']}]({r['model_url']})"
        rows.append({
            "Model": model_name,
            "Org": r["org"],
            "Type": r["type"],
            "Params (B)": r["params_b"] if r["params_b"] else "—",
            "Recall@1 (%)": r["recall_1"] if r["recall_1"] is not None else "—",
            "Recall@5 (%)": r["recall_5"] if r["recall_5"] is not None else "—",
            "MRR": f"{r['mrr']:.2f}" if r.get("mrr") else "—",
            "Mean Score": f"{r['mean_score']:.3f}" if r.get("mean_score") else "—",
            "Open": "Yes" if r["open_source"] else "No",
            "Source": r["source"].capitalize(),
            "Date": r["submitted"],
        })
    df = pd.DataFrame(rows)
    # Sort by Recall@1 descending, with "—" values last
    df["_sort"] = df["Recall@1 (%)"].apply(lambda x: float(x) if x != "—" else -1)
    df = df.sort_values("_sort", ascending=False).drop(columns=["_sort"])
    return df


def get_metadata() -> dict:
    """Load benchmark metadata."""
    data = json.loads(RESULTS_PATH.read_text())
    return data["metadata"]


# ---------------------------------------------------------------------------
# Branding
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
.disclaimer-banner {
    background: linear-gradient(135deg, #D4A84B 0%, #C49A3D 100%);
    color: #1B2A4A;
    padding: 12px 20px;
    border-radius: 8px;
    font-weight: 600;
    margin-bottom: 16px;
    text-align: center;
    font-size: 14px;
}
.leaderboard-header {
    text-align: center;
    padding: 20px 0 8px 0;
}
.leaderboard-header h1 {
    color: #1B2A4A;
    font-size: 28px;
    margin-bottom: 4px;
}
.leaderboard-subtitle {
    color: #2E8B8B;
    font-size: 16px;
    text-align: center;
    margin-bottom: 16px;
}
.source-note {
    background: #f0f4f8;
    border-left: 3px solid #2E8B8B;
    padding: 10px 14px;
    border-radius: 0 6px 6px 0;
    margin: 12px 0;
    font-size: 13px;
}
.footer-text {
    text-align: center;
    color: #666;
    font-size: 13px;
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid #e0e0e0;
}
"""

# ---------------------------------------------------------------------------
# Tab Content
# ---------------------------------------------------------------------------

DISCLAIMER = (
    '<div class="disclaimer-banner">'
    "Research Use Only — This leaderboard evaluates diagnostic AI models on "
    "research benchmarks. No model listed here has been validated for clinical "
    "use or cleared by any regulatory authority."
    "</div>"
)

LEADERBOARD_HEADER = """
<div class="leaderboard-header">
<h1>Rare Archive Diagnosis Leaderboard</h1>
</div>
<div class="leaderboard-subtitle">
Open benchmarks for rare disease diagnostic AI · No disease is too rare to matter
</div>
"""

BENCHMARK_TAB = """
## RareArena Benchmark

**Task**: Clinical vignette → ranked differential diagnosis (up to 5 candidates).

The benchmark evaluates a model's ability to read a clinical presentation — symptoms, history,
lab results — and produce an accurate, ranked differential diagnosis for rare diseases.

### Dataset

| Split | Description | Eval Cases |
|-------|-------------|------------|
| **RDS** | Full clinical vignettes with HPO phenotypes | ~80 |
| **RDC** | Vignettes with test results (labs, imaging) | ~40 |
| **IEM** | Metabolic disease focus with biochemical markers | ~50 |
| **NMD** | Neuromuscular disease focus | ~30 |
| **Total** | **Held-out evaluation set** | **~200** |

Training data: ~69,000 examples from RareArena + synthetic patients across 9,100+ diseases.

Published datasets:
- [`rare-archive-eval-rarearena-rds`](https://huggingface.co/datasets/wilhelm-foundation/rare-archive-eval-rarearena-rds) (8,562 records)
- [`rare-archive-eval-rarearena-rdc`](https://huggingface.co/datasets/wilhelm-foundation/rare-archive-eval-rarearena-rdc) (4,376 records)
- [`rare-archive-synthetic-patients`](https://huggingface.co/datasets/wilhelm-foundation/rare-archive-synthetic-patients) (12,984 records)

### Metrics

| Metric | Definition | Range |
|--------|-----------|-------|
| **Recall@1** | First diagnosis matches ground truth | 0–100% |
| **Recall@5** | Ground truth in top 5 diagnoses | 0–100% |
| **MRR** | Mean Reciprocal Rank — 1 / rank of first correct | 0–1.0 |
| **Mean Score** | Semantic similarity (0 = wrong, 1 = partial, 2 = correct) | 0–2.0 |

### Scoring Protocol

Models generate up to 5 ranked diagnoses per clinical vignette. Each diagnosis is scored:

| Score | Meaning |
|-------|---------|
| **2** | Correct — matches ground truth diagnosis |
| **1** | Partial — related condition or correct disease family |
| **0** | Incorrect — wrong diagnosis |

Scoring uses structured field matching with word overlap fallback.
Primary scorer: GPT-4o semantic evaluation. Fallback: string matching + 50% word intersection threshold.

### Compared to Other Benchmarks

| Benchmark | Diseases | Cases | Metrics | Open Data |
|-----------|----------|-------|---------|-----------|
| **RareArena (ours)** | **9,100+** | **~50K** | Recall@1/5, MRR, Mean | **Yes** |
| RareBench (KDD 2024) | 421 | 2,185 | Top-1/3/10 recall | Yes |
| RareScale (arXiv 2025) | 575 | 43,162 (synthetic) | Top-1/5, MRR | No |
| DeepRare (Nature 2026) | 2,919 | 6,401 | Recall@1/3/5 | Partial |

RareArena is the **largest open rare disease evaluation dataset** by both disease count and case count.
"""

SUBMIT_TAB = """
## Submit a Model

We welcome submissions from the community. Three tracks are available:

### Track A: HuggingFace Model
Submit a public HuggingFace model ID. We run inference + scoring on our evaluation cluster.

**Requirements**:
- Model must be public on HuggingFace
- Safetensors format, loadable via `AutoModelForCausalLM`
- Max 100B parameters (float16) or 560B (4-bit quantized)

### Track B: Pre-computed Results
Upload a JSONL file with your model's predictions on our public eval set.

**Format**:
```json
{"case_id": "rds_001", "diagnoses": ["Gaucher disease type 1", "Fabry disease", "Niemann-Pick C"]}
{"case_id": "rds_002", "diagnoses": ["Duchenne muscular dystrophy", "Becker MD", "SMA type 2"]}
```

### Track C: API Endpoint
Provide an HTTP endpoint. We send vignettes, you return diagnoses.

```
POST https://your-api.com/diagnose
{"clinical_vignette": "..."}
→ {"diagnoses": ["...", "...", "..."]}
```

### Submission Guidelines

- **Rate limit**: 3 submissions per month per user per track
- **Attribution**: HuggingFace login required
- **Disclosure**: You must report whether the model uses external tools during inference
- **Transparency**: Training data description required (high-level)
- All submissions are public (model name, org, scores, date)
- Prediction files are kept private (benchmark integrity)

### How to Submit

**V1 (current)**: Email submissions to **rare-archive@wilhelm.foundation** with:
1. Model name and organization
2. Track (A, B, or C)
3. Model link (HuggingFace, GitHub, or API endpoint)
4. Training data description
5. Whether the model uses tools during inference

**V2 (planned)**: Self-service submission form with automated evaluation.
"""

ABOUT_TAB = """
## About

### Mission

The Rare Archive Diagnosis Leaderboard provides **open, transparent benchmarks** for rare disease
diagnostic AI. 300 million people worldwide live with a rare disease, and the average diagnostic
odyssey takes 5–7 years. AI can help — but only if we can measure progress honestly.

This leaderboard exists because:
- **No public rare disease AI leaderboard existed** before this one
- Benchmark results published in papers are not directly comparable across systems
- The rare disease community deserves transparency about what AI can and cannot do
- Progress requires measurement, and measurement requires shared standards

### What This Leaderboard Is

A research benchmark comparing models on standardized evaluation tasks. Higher rankings indicate
better performance on the RareArena benchmark, which measures diagnostic accuracy on clinical
vignettes.

### What This Leaderboard Is Not

A clinical validation. **No model on this leaderboard has been validated for clinical use, cleared
by any regulatory authority, or approved as a medical device.** Benchmark performance does not
predict real-world clinical performance. Models may perform differently on patient populations not
represented in the evaluation data.

### Ethical Framework

- **Bias transparency**: Per-category breakdowns reveal where models fail. If a model scores 40%
  on metabolic diseases but 5% on neuromuscular, that variance is published — not hidden.
- **Failure mode documentation**: The benchmark includes ultra-rare diseases, overlapping phenotypes,
  and incomplete presentations where all models struggle.
- **No ranking implies endorsement**: Higher rankings do not imply clinical safety.
- **Contamination prevention**: Evaluation test set is private. Submissions are rate-limited.
  Suspiciously high scores are flagged for manual review.

### Related Work

- Chen et al. (2024). "[RareBench: Can LLMs Serve as Rare Diseases Specialists?](https://arxiv.org/abs/2402.06341)" KDD 2024.
- Shlain et al. (2025). "[Rare Disease Differential Diagnosis at Scale](https://arxiv.org/abs/2502.15069)." arXiv.
- Zhao et al. (2026). "[DeepRare: Agentic Rare Disease Diagnosis](https://arxiv.org/abs/2506.20430)." Nature.

### Citation

If you use this leaderboard or the RareArena benchmark in your work, please cite:

```bibtex
@misc{rare-archive-leaderboard-2026,
  title={Rare Archive Diagnosis Leaderboard},
  author={Wilhelm Foundation and Lattice Protocol},
  year={2026},
  url={https://huggingface.co/spaces/wilhelm-foundation/rare-archive-leaderboard},
  note={Open benchmarks for rare disease diagnostic AI}
}
```

### Team

A program of the **[Wilhelm Foundation](https://wilhelm.foundation)**, built with the
**[Lattice Protocol](https://github.com/LatticeProtocol)**.

- GitHub: [Wilhelm-Foundation/rare-archive](https://github.com/Wilhelm-Foundation/rare-archive)
- HuggingFace: [wilhelm-foundation](https://huggingface.co/wilhelm-foundation)
- Model: [rare-archive-qwen-4b-sft-v1](https://huggingface.co/wilhelm-foundation/rare-archive-qwen-4b-sft-v1)
"""

FOOTER = (
    '<div class="footer-text">'
    "A program of the <b>Wilhelm Foundation</b> · "
    'Built with the <a href="https://github.com/LatticeProtocol">Lattice Protocol</a> · '
    '<a href="https://github.com/Wilhelm-Foundation/rare-archive">GitHub</a> · '
    '<a href="https://huggingface.co/wilhelm-foundation">HuggingFace</a>'
    "</div>"
)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

with gr.Blocks(
    title="Rare Archive Diagnosis Leaderboard",
    theme=gr.themes.Soft(),
    css=CUSTOM_CSS,
) as demo:

    gr.HTML(DISCLAIMER)
    gr.HTML(LEADERBOARD_HEADER)

    with gr.Tabs():

        # -- Tab 1: Leaderboard --
        with gr.TabItem("Leaderboard"):
            df = load_results()
            meta = get_metadata()

            gr.Markdown(
                f"**{len(df)} models** evaluated on "
                f"**RareArena** ({meta['eval_cases']} held-out cases, "
                f"{meta['diseases']} diseases)"
            )

            leaderboard_table = gr.Dataframe(
                value=df,
                headers=list(df.columns),
                datatype=[
                    "markdown", "str", "str", "str",
                    "str", "str", "str", "str",
                    "str", "str", "str",
                ],
                interactive=False,
                wrap=True,
            )

            gr.HTML(
                '<div class="source-note">'
                "<b>Source key</b>: "
                "<b>Evaluated</b> = scored on RareArena held-out test set. "
                "<b>Literature</b> = scores reported from published papers on "
                "different benchmarks — included for context but not directly comparable."
                "</div>"
            )

        # -- Tab 2: Benchmark --
        with gr.TabItem("Benchmark"):
            gr.Markdown(BENCHMARK_TAB)

        # -- Tab 3: Submit --
        with gr.TabItem("Submit"):
            gr.Markdown(SUBMIT_TAB)

        # -- Tab 4: About --
        with gr.TabItem("About"):
            gr.Markdown(ABOUT_TAB)

    gr.HTML(FOOTER)

demo.launch()
