"""Schema validation for Rare Archive ontology domains."""

import json
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import Draft202012Validator


SCHEMA_DIR = Path(__file__).parent.parent.parent / "schemas"

_SCHEMA_CACHE: dict[str, dict] = {}


def _load_schema(name: str) -> dict:
    """Load a JSON schema by domain name."""
    if name not in _SCHEMA_CACHE:
        schema_path = SCHEMA_DIR / f"{name}.schema.json"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {schema_path}")
        with open(schema_path) as f:
            _SCHEMA_CACHE[name] = json.load(f)
    return _SCHEMA_CACHE[name]


def validate_patient_category(data: dict[str, Any]) -> list[str]:
    """Validate a patient category against its schema. Returns list of errors."""
    return _validate(data, "patient_category")


def validate_clinical_tool(data: dict[str, Any]) -> list[str]:
    """Validate a clinical tool against its schema. Returns list of errors."""
    return _validate(data, "clinical_tool")


def validate_model(data: dict[str, Any]) -> list[str]:
    """Validate a model against its schema. Returns list of errors."""
    return _validate(data, "model")


def validate_dataset(data: dict[str, Any]) -> list[str]:
    """Validate a dataset against its schema. Returns list of errors."""
    return _validate(data, "dataset")


def _validate(data: dict[str, Any], schema_name: str) -> list[str]:
    """Validate data against a named schema. Returns list of error messages."""
    schema = _load_schema(schema_name)
    validator = Draft202012Validator(schema)
    return [e.message for e in validator.iter_errors(data)]
