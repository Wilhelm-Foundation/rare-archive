# Rare Archive Compliance

aDNA schema validation, FAIR scoring, and governance for the [Rare AI Archive](https://github.com/wilhelm-foundation/rare-ai-archive).

## Schemas

### aDNA Envelopes
- `schemas/adna/rare_envelope.schema.json` — Base aDNA envelope with `rare_` namespace
- `schemas/adna/rare_module.schema.json` — Module-specific (models, tools)
- `schemas/adna/rare_dataset.schema.json` — Dataset-specific (PHI governance)

### FAIR Scoring
- `schemas/fair/archive_fair_criteria.json` — 6 Archive-specific criteria extending Lattice Protocol's 16

## GitHub Action

Add to any Rare Archive repo's CI:

```yaml
- uses: wilhelm-foundation/rare-archive-compliance/action@main
  with:
    fail-on-fair-score: 50
```

## Python Library

```python
from rare_archive_compliance.validator import validate_adna_envelope, validate_adna_triad
from rare_archive_compliance.fair_scorer import score_artifact

# Validate aDNA structure
errors = validate_adna_triad(Path("./my-repo"))

# Score an artifact
result = score_artifact(metadata_dict)
print(f"FAIR score: {result['total_score']}/100")
print(f"Publication ready: {result['publication_ready']}")
```

## License

Apache 2.0
