"""Rare AI Archive — RareArena Leaderboard
Automated evaluation results on the RareArena benchmark.
"""

import gradio as gr

BENCHMARK_RESULTS = [
    {
        "model": "GPT-4o (baseline)",
        "top_1": 33.1,
        "top_5": 52.4,
        "mean_score": 0.85,
        "source": "RareArena paper",
    },
    {
        "model": "Deep-DxSearch",
        "top_1": 70.48,
        "top_5": 82.1,
        "mean_score": 1.52,
        "source": "Deep-DxSearch paper",
    },
    {
        "model": "Qwen3.5-4B (base)",
        "top_1": 0.0,
        "top_5": 0.0,
        "mean_score": 0.0,
        "source": "Pending evaluation",
    },
    {
        "model": "Qwen3.5-4B (SFT Stage 1)",
        "top_1": 0.0,
        "top_5": 0.0,
        "mean_score": 0.0,
        "source": "Pending training",
    },
]


def get_results():
    return [
        [r["model"], r["top_1"], r["top_5"], r["mean_score"], r["source"]]
        for r in sorted(BENCHMARK_RESULTS, key=lambda x: x["top_1"], reverse=True)
    ]


with gr.Blocks(
    title="Rare AI Archive — RareArena Leaderboard",
    theme=gr.themes.Soft(),
) as demo:
    gr.Markdown("""
    # RareArena Leaderboard

    Benchmark results on [RareArena](https://huggingface.co/datasets/RareArena) (~50K cases, 4K+ diseases).

    **Evaluation protocol:** Generate top-5 diagnoses -> GPT-4o scoring (0=wrong, 1=partial, 2=correct)

    *A program of the [Wilhelm Foundation](https://wilhelm.foundation)*
    """)

    results = gr.Dataframe(
        headers=["Model", "Top-1 Acc (%)", "Top-5 Acc (%)", "Mean Score", "Source"],
        value=get_results(),
        label="Benchmark Results",
        interactive=False,
    )

    gr.Markdown("""
    ### Scoring

    | Score | Meaning |
    |-------|---------|
    | 2 | Correct — matches ground truth diagnosis |
    | 1 | Partial — related condition or correct disease family |
    | 0 | Incorrect — wrong diagnosis |

    Top-1 accuracy measures exact match of the highest-ranked diagnosis.
    Mean score averages the best score across all top-5 predictions.
    """)

demo.launch()
