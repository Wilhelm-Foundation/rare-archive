"""Rare AI Archive — Clinical Demo Space

Interactive demonstration of rare disease diagnostic reasoning with
tool-augmented clinical assessment. All responses are pre-computed from
the Rare Disease Specialist model running on L2 infrastructure.

Research use only. All patient data is synthetic.
"""

import json
from pathlib import Path

import gradio as gr

# ---------------------------------------------------------------------------
# Load pre-computed responses
# ---------------------------------------------------------------------------

DATA_PATH = Path(__file__).parent / "responses.json"
with open(DATA_PATH) as f:
    DATA = json.load(f)

SCENARIOS = {s["id"]: s for s in DATA["scenarios"]}

# Build dropdown choices grouped by category
CATEGORY_ORDER = [
    "Inborn Errors of Metabolism",
    "Inborn Errors of Metabolism (Mitochondrial)",
    "Inborn Errors of Metabolism (Lysosomal Storage)",
    "Neuromuscular",
    "Connective Tissue",
    "Immunodeficiency",
    "Complex Genetic (Multi-System)",
]


def build_choices():
    """Build scenario dropdown choices."""
    choices = []
    for scenario in DATA["scenarios"]:
        label = f"[{scenario['category']}] {scenario['title']}"
        choices.append((label, scenario["id"]))
    return choices


CHOICES = build_choices()


# ---------------------------------------------------------------------------
# Callback functions
# ---------------------------------------------------------------------------


def load_scenario(scenario_id):
    """Load a scenario and return all display components."""
    if scenario_id is None:
        return (
            gr.update(value="*Select a scenario above to begin.*"),
            gr.update(value="", visible=False),
            gr.update(visible=False),
            gr.update(value="", visible=False),
        )

    s = SCENARIOS[scenario_id]

    # Patient presentation
    presentation = (
        f"### {s['title']}\n"
        f"**Category**: {s['category']} · **Complexity**: {s['complexity']}\n\n"
        f"> {s['patient_presentation']}"
    )

    # Tool results — build accordion content
    tools_md = ""
    for tc in s["tool_calls"]:
        tools_md += f"### {tc['tool']}\n"
        tools_md += f"`{tc['query']}`\n\n"
        tools_md += f"{tc['result']}\n\n---\n\n"

    # Clinical assessment
    assessment = s["clinical_assessment"]

    return (
        gr.update(value=presentation),
        gr.update(value=tools_md, visible=True),
        gr.update(visible=True),
        gr.update(value=assessment, visible=True),
    )


# ---------------------------------------------------------------------------
# UI Layout
# ---------------------------------------------------------------------------

THEME = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="slate",
    neutral_hue="slate",
)

CSS = """
.disclaimer {
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 16px;
    font-size: 0.9em;
    color: #856404;
}
.disclaimer-dark {
    background: #332d00;
    border-color: #665a00;
    color: #ffc107;
}
footer { display: none !important; }
"""

with gr.Blocks(
    title="Rare AI Archive — Clinical Demo",
    theme=THEME,
    css=CSS,
) as demo:
    # Header
    gr.Markdown("""
# Rare AI Archive — Clinical Demo

Explore how AI-assisted rare disease diagnostics works. Select a clinical
scenario to see the full diagnostic workflow: patient presentation, clinical
tool queries, and structured clinical assessment.

**10 scenarios** across 6 disease categories — from newborn screening to
complex multi-system disorders.
    """)

    gr.HTML("""
<div class="disclaimer">
    <strong>Research Use Only.</strong> All patient data is synthetic.
    This is not a diagnostic tool — outputs require clinical validation.
    Responses are pre-computed from the Rare Disease Specialist model.
</div>
    """)

    with gr.Tabs():
        # ---------------------------------------------------------------
        # Tab 1: Clinical Demo
        # ---------------------------------------------------------------
        with gr.TabItem("Clinical Demo", id="demo"):
            scenario_dropdown = gr.Dropdown(
                choices=CHOICES,
                label="Select Clinical Scenario",
                info="Choose a rare disease case to explore the diagnostic workflow",
                value=None,
                interactive=True,
            )

            presentation_md = gr.Markdown(
                value="*Select a scenario above to begin.*",
                label="Patient Presentation",
            )

            with gr.Accordion(
                "Clinical Tool Results (click to expand)",
                open=False,
                visible=False,
            ) as tools_accordion:
                tools_md = gr.Markdown(value="", visible=False)

            assessment_md = gr.Markdown(
                value="",
                visible=False,
                label="Clinical Assessment",
            )

            scenario_dropdown.change(
                fn=load_scenario,
                inputs=[scenario_dropdown],
                outputs=[presentation_md, tools_md, tools_accordion, assessment_md],
            )

        # ---------------------------------------------------------------
        # Tab 2: About
        # ---------------------------------------------------------------
        with gr.TabItem("About", id="about"):
            gr.Markdown("""
## About the Rare AI Archive

300 million people worldwide live with a rare disease. The average diagnostic
odyssey takes 5–7 years. The **Rare AI Archive** exists to close that gap.

### What This Demo Shows

Each scenario demonstrates the full diagnostic workflow:

1. **Patient Presentation** — A clinical vignette describing symptoms,
   lab results, and genetic findings
2. **Clinical Tool Queries** — The model queries 7 specialized databases
   (Orphanet, ClinVar, gnomAD, PanelApp, HPO, PubMed, DiffDx) to gather
   evidence
3. **Clinical Assessment** — A structured diagnostic report with evidence
   synthesis, management recommendations, and genetic counseling points

### Models

| Model | Status | Description |
|-------|--------|-------------|
| **Qwen 4B SFT v1** | Published | 21.5% Top-1 accuracy, GGUF for local inference |
| **Qwen 35B MoE SFT** | Training | 35B parameters (3B active), for research clusters |

### Architecture

The system uses 7 clinical tool adapters for evidence-based reasoning:

- **Orphanet** — Disease information, prevalence, genetics
- **ClinVar** — Variant pathogenicity classification
- **gnomAD** — Population allele frequencies
- **PanelApp** — Gene panels for suspected conditions
- **HPO** — Human Phenotype Ontology mapping
- **PubMed** — Literature search
- **DiffDx** — Structured differential diagnosis

### Links

- [GitHub Repository](https://github.com/Wilhelm-Foundation/rare-archive)
- [HuggingFace Models](https://huggingface.co/Wilhelm-Foundation)
- [4B Model (GGUF)](https://huggingface.co/Wilhelm-Foundation/rare-archive-qwen-4b-sft-v1)
- [Contributing Guide](https://github.com/Wilhelm-Foundation/rare-archive/blob/main/CONTRIBUTING.md)

### Credits

A program of the [Wilhelm Foundation](https://wilhelm.foundation).
Built on [Lattice Protocol](https://github.com/LatticeProtocol) infrastructure.

*Built by people who believe that no disease is too rare to matter.*
            """)

demo.launch()
