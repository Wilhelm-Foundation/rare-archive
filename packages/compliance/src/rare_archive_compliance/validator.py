"""aDNA envelope and schema validation for Rare AI Archive artifacts."""

import json
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import Draft202012Validator


SCHEMA_DIR = Path(__file__).parent.parent.parent / "schemas"


def _load_schema(schema_path: Path) -> dict:
    """Load a JSON schema file."""
    with open(schema_path) as f:
        return json.load(f)


def validate_adna_envelope(data: dict[str, Any]) -> list[str]:
    """Validate an artifact's aDNA envelope against the rare_envelope schema.

    Returns list of validation error messages. Empty list means valid.
    """
    schema = _load_schema(SCHEMA_DIR / "adna" / "rare_envelope.schema.json")
    validator = Draft202012Validator(schema)
    return [e.message for e in validator.iter_errors(data)]


def validate_adna_triad(repo_path: Path) -> list[str]:
    """Validate that a repository has the required aDNA triad structure.

    Checks for .agentic/what/, .agentic/how/, .agentic/who/ directories
    and required AGENTS.md files.
    """
    errors = []
    agentic = repo_path / ".agentic"

    if not agentic.is_dir():
        return [f"Missing .agentic/ directory in {repo_path}"]

    for triad in ["what", "how", "who"]:
        triad_dir = agentic / triad
        if not triad_dir.is_dir():
            errors.append(f"Missing .agentic/{triad}/ directory")
        agents_md = triad_dir / "AGENTS.md"
        if not agents_md.is_file():
            errors.append(f"Missing .agentic/{triad}/AGENTS.md")

    root_agents = agentic / "AGENTS.md"
    if not root_agents.is_file():
        errors.append("Missing .agentic/AGENTS.md")

    return errors


def validate_naming_convention(name: str, context: str = "file") -> list[str]:
    """Validate naming conventions per Lattice Protocol rules.

    Files use underscores. HuggingFace-facing names use hyphens.
    """
    errors = []

    if context == "file":
        if "-" in name:
            errors.append(
                f"File name '{name}' contains hyphens — use underscores per naming convention"
            )
    elif context == "huggingface":
        if "_" in name:
            errors.append(
                f"HuggingFace name '{name}' contains underscores — use hyphens per ADR"
            )

    if name != name.lower():
        errors.append(f"Name '{name}' is not lowercase")

    return errors
