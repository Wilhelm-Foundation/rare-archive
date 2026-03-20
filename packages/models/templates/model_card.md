---
library_name: transformers
base_model: {{ base_model }}
license: apache-2.0
tags:
  - rare-disease
  - clinical-diagnostics
  - lora
  - rare-archive
  - {{ model_size }}
  - {{ training_stage }}
language:
  - en
pipeline_tag: text-generation
---

# {{ model_name }}

A LoRA adapter fine-tuned for rare disease diagnostic reasoning.

**Part of the [Rare AI Archive](https://github.com/Wilhelm-Foundation/rare-archive)** — a decentralized post-training ecosystem for rare genetic diseases.

## Model Details

| Property | Value |
|----------|-------|
| Base model | {{ base_model }} |
| Architecture | {{ architecture }} |
| Training stage | {{ training_stage_name }} |
| LoRA rank | {{ lora_rank }} |
| Patient category | {{ patient_category }} |
| Framework | {{ framework }} |

## Training

{{ training_description }}

## Evaluation

### RareArena Results

| Metric | Score |
|--------|-------|
| Top-1 Accuracy | {{ top_1_accuracy }}% |
| Top-5 Accuracy | {{ top_5_accuracy }}% |
| Mean Score | {{ mean_score }} |

## Usage

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

base = AutoModelForCausalLM.from_pretrained("{{ base_model }}")
model = PeftModel.from_pretrained(base, "wilhelm-foundation/{{ model_name }}")
tokenizer = AutoTokenizer.from_pretrained("{{ base_model }}")
```

## Intended Use

This model is intended for **research and educational purposes** in rare disease diagnostics. It should not be used as a sole diagnostic tool in clinical settings.

## Limitations

- Trained on synthetic patient data only (no real PHI)
- Performance varies across disease categories
- Should always be used alongside clinical expertise

## Citation

```bibtex
@misc{rare-archive-{{ model_name }},
  title={{{ model_name }}},
  author={Wilhelm Foundation},
  year={2026},
  publisher={HuggingFace},
  url={https://huggingface.co/wilhelm-foundation/{{ model_name }}}
}
```
