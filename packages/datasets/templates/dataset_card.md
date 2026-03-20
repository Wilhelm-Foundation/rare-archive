---
dataset_info:
  name: {{ name }}
  version: {{ version }}
  license: {{ license }}
  description: {{ description }}
tags:
  - rare-disease
  - clinical-diagnostics
  - {{ dataset_type }}
  - rare-archive
task_categories:
  - text-generation
  - question-answering
language:
  - en
size_categories:
  - {{ size_category }}
---

# {{ name }}

{{ description }}

## Dataset Description

- **Repository:** [wilhelm-foundation/{{ name }}](https://huggingface.co/datasets/wilhelm-foundation/{{ name }})
- **License:** {{ license }}
- **Version:** {{ version }}
- **Part of:** [Rare AI Archive](https://github.com/Wilhelm-Foundation/rare-archive)

## Dataset Structure

### Data Fields

{{ field_descriptions }}

### Data Splits

| Split | Records |
|-------|---------|
{{ split_table }}

## Dataset Creation

### Source Data

{{ source_description }}

### Data Processing

{{ processing_description }}

### PHI Status

**{{ phi_status }}** — {{ phi_description }}

## Patient Categories

This dataset covers the following patient categories:

{{ category_list }}

## Intended Use

{{ intended_use }}

## Limitations

{{ limitations }}

## Citation

If you use this dataset, please cite:

```bibtex
@misc{rare-archive-{{ name }},
  title={{{ name }}},
  author={Wilhelm Foundation},
  year={2026},
  publisher={HuggingFace},
  url={https://huggingface.co/datasets/wilhelm-foundation/{{ name }}}
}
```
