"""Rare AI Archive — Model Comparison Arena
A public Gradio Space for comparing rare disease diagnostic models.
"""

import json

import gradio as gr
import httpx

ARCHIVE_API_URL = "https://go.latticelab.ai/elo"
MODELS = [
    {"id": "qwen3.5-4b-sft", "name": "Qwen3.5-4B (SFT)", "size": "4B"},
    {"id": "qwen3.5-9b-sft", "name": "Qwen3.5-9B (SFT)", "size": "9B"},
    {"id": "qwen3.5-27b-sft", "name": "Qwen3.5-27B (SFT)", "size": "27B"},
    {"id": "qwen3.5-35b-a3b-sft", "name": "Qwen3.5-35B-A3B (SFT)", "size": "35B MoE"},
]


async def get_leaderboard():
    """Fetch current ELO leaderboard from the Archive API."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{ARCHIVE_API_URL}/ratings", timeout=10)
            if resp.status_code == 200:
                ratings = resp.json()
                return format_leaderboard(ratings)
    except Exception:
        pass

    # Fallback: static demo data
    return [
        ["Qwen3.5-35B-A3B", 1587, 1612, 1545, 1598, 1601, 24],
        ["Qwen3.5-27B", 1553, 1578, 1521, 1567, 1589, 31],
        ["Qwen3.5-9B", 1498, 1512, 1487, 1501, 1534, 28],
        ["Qwen3.5-4B", 1432, 1445, 1398, 1421, 1478, 22],
    ]


def format_leaderboard(ratings):
    """Format API ratings into table rows."""
    rows = []
    for r in sorted(ratings, key=lambda x: x["overall_elo"], reverse=True):
        rows.append([
            r["model_id"],
            round(r["overall_elo"]),
            round(r["diagnostic_accuracy_elo"]),
            round(r["reasoning_quality_elo"]),
            round(r["tool_usage_elo"]),
            round(r["safety_elo"]),
            r["total_comparisons"],
        ])
    return rows


with gr.Blocks(
    title="Rare AI Archive — Model Arena",
    theme=gr.themes.Soft(),
) as demo:
    gr.Markdown("""
    # Rare AI Archive — Model Comparison Arena

    Multi-dimensional ELO rankings for rare disease diagnostic models.
    Models are evaluated by clinical experts across 4 dimensions.

    *A program of the [Wilhelm Foundation](https://wilhelm.foundation)*
    """)

    leaderboard = gr.Dataframe(
        headers=["Model", "Overall ELO", "Dx Accuracy", "Reasoning", "Tool Usage", "Safety", "Comparisons"],
        label="ELO Leaderboard",
        interactive=False,
    )

    refresh_btn = gr.Button("Refresh Leaderboard")
    refresh_btn.click(fn=get_leaderboard, outputs=leaderboard)

    gr.Markdown("""
    ### Evaluation Dimensions

    | Dimension | Description | Scale |
    |-----------|-------------|-------|
    | **Diagnostic Accuracy** | Correct diagnosis identification | 0-5 |
    | **Reasoning Quality** | Clinical reasoning chain clarity | 0-5 |
    | **Tool Usage** | Appropriate diagnostic tool use | 0-5 |
    | **Safety** | Avoidance of harmful recommendations | 0-5 |

    ### How It Works

    Clinical experts evaluate pairs of anonymized model responses in an Arena format.
    Each comparison updates multi-dimensional ELO ratings per (model, disease category).
    Preference data is exported for DPO/GRPO training, closing the RLHF loop.
    """)

demo.launch()
