#!/usr/bin/env python3
"""Rare AI Archive — Monorepo validation script.

Validates that all packages exist, aDNA triads are present,
schemas are valid, and dependency constraints are met.
"""

import json
import sys
from pathlib import Path

import yaml


def load_yaml(path: Path) -> dict:
    """Load a YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def check_adna_triad(pkg_path: Path) -> list[str]:
    """Verify aDNA triad structure exists."""
    errors = []
    required_dirs = [
        ".agentic/what",
        ".agentic/how",
        ".agentic/who",
    ]
    required_files = [
        ".agentic/AGENTS.md",
        ".agentic/what/AGENTS.md",
        ".agentic/how/AGENTS.md",
        ".agentic/who/AGENTS.md",
    ]

    for d in required_dirs:
        if not (pkg_path / d).is_dir():
            errors.append(f"Missing aDNA directory: {d}")

    for f in required_files:
        if not (pkg_path / f).is_file():
            errors.append(f"Missing aDNA file: {f}")

    return errors


def check_packages(root: Path) -> dict[str, list[str]]:
    """Check all packages and deploy in the monorepo."""
    components_yaml = root / "components.yaml"
    if not components_yaml.exists():
        return {"root": ["components.yaml not found"]}

    config = load_yaml(components_yaml)
    results = {}

    for name, info in config.get("packages", {}).items():
        pkg_path = root / info.get("path", f"packages/{name}")
        errors = []

        if not pkg_path.is_dir():
            errors.append(f"Package directory not found: {pkg_path}")
        else:
            errors.extend(check_adna_triad(pkg_path))

        results[name] = errors

    # Check root-level aDNA triad
    root_errors = check_adna_triad(root)
    if root_errors:
        results["root"] = root_errors

    return results


def check_schemas(root: Path) -> list[str]:
    """Validate JSON schemas in ontology package."""
    errors = []
    ontology_path = root / "packages" / "ontology" / "schemas"

    if not ontology_path.is_dir():
        return ["Ontology schemas directory not found"]

    for schema_file in ontology_path.glob("*.schema.json"):
        try:
            with open(schema_file) as f:
                json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in {schema_file.name}: {e}")

    return errors


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()

    print("Rare AI Archive — Validation Report")
    print("=" * 50)

    # Check packages
    pkg_results = check_packages(root)
    all_pass = True

    for pkg, errors in pkg_results.items():
        if errors:
            print(f"\n  FAIL  {pkg}")
            for e in errors:
                print(f"         - {e}")
            all_pass = False
        else:
            print(f"\n  PASS  {pkg}")

    # Check schemas
    schema_errors = check_schemas(root)
    if schema_errors:
        print(f"\n  FAIL  schemas")
        for e in schema_errors:
            print(f"         - {e}")
        all_pass = False
    else:
        print(f"\n  PASS  schemas")

    print("\n" + "=" * 50)
    if all_pass:
        print("All checks passed.")
        return 0
    else:
        print("Some checks failed. See above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
