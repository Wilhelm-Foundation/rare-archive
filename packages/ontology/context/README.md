# Context Files — Expert Diagnostic Knowledge

Context files capture the **tacit reasoning** that rare disease specialists bring to diagnosis — the "why" behind tool selection, the interpretation rules for database outputs, and the diagnostic workflow patterns that exist in expert minds but not yet in training data.

## What Context Files Are

A context file is structured knowledge about **how to reason** with clinical tools for rare disease diagnostics. This is distinct from clinical vignettes (cases to reason *about*) or tool documentation (what a tool *does*).

Context files capture knowledge like:
- "Check ClinVar *before* gnomAD for this disease because the pathogenic variants are well-characterized"
- "Use the Ashkenazi Jewish subpopulation in gnomAD, not the overall frequency"
- "When Orphanet returns multiple matches, prioritize by inheritance pattern match"

## Categories

| Category | What It Captures | Primary Contributors |
|----------|-----------------|---------------------|
| `diagnostic_workflow` | Step-by-step reasoning from presentation to diagnosis | Clinicians |
| `interpretation_guide` | How to read and act on tool/database outputs | Clinicians, Computational Biologists |
| `data_source_guide` | Which databases matter, version caveats, reliability | Computational Biologists |
| `tool_sequence` | Recommended tool invocation order with branching logic | Computational Biologists |
| `phenotype_pattern` | Clinical feature clusters with gene-disease mappings | Genetic Counselors |
| `diagnostic_odyssey` | Patient journey lessons, common misdiagnoses | Patient Advocates |

## Directory Structure

```
context/
├── README.md                                          # This file
├── rare_ctx_datasource_nanopore_longread.yaml         # Exemplar: data source guide
├── rare_ctx_workflow_lsd_gaucher.yaml                 # Exemplar: diagnostic workflow
├── lsd/                                               # Future: Lysosomal Storage Disease cluster
├── neuromuscular/                                     # Future: Neuromuscular Disorders cluster
└── iem/                                               # Future: Inborn Errors of Metabolism cluster
```

## File Naming Convention

```
rare_ctx_[category_short]_[disease_area]_[descriptor].yaml
```

Category abbreviations: `workflow`, `interp`, `datasource`, `toolseq`, `phenotype`, `odyssey`.

## Schema

All context files validate against [`../schemas/context_file.schema.json`](../schemas/context_file.schema.json).

Required fields: `context_id`, `title`, `version`, `category`, `description`, `when_to_use`.

## Quality Tiers

| Tier | Meaning | Use |
|------|---------|-----|
| `draft` | Captured but not reviewed | Internal reference only |
| `reviewed` | 2+ specialist sign-off | OpenWebUI knowledge grounding |
| `validated` | Reviewed + schema valid + novelty assessed | Training annotation |
| `published` | Committed with FAIR metadata | Production use |

## Contributing

See the "Contributing Context Files" section in [CONTRIBUTING.md](../../../CONTRIBUTING.md) for how to submit context files.
