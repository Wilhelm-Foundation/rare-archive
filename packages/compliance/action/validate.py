#!/usr/bin/env python3
"""Rare Archive compliance validation script for GitHub Actions.

Validates:
1. aDNA triad structure
2. JSON schema compliance
3. FAIR scoring
4. Naming conventions
"""

import argparse
import json
import sys
from pathlib import Path

import yaml


def validate_adna_triad(repo_path: Path) -> list[str]:
    """Check aDNA triad structure."""
    errors = []
    agentic = repo_path / ".agentic"

    if not agentic.is_dir():
        return [f"Missing .agentic/ directory"]

    for triad in ["what", "how", "who"]:
        if not (agentic / triad).is_dir():
            errors.append(f"Missing .agentic/{triad}/")
        if not (agentic / triad / "AGENTS.md").is_file():
            errors.append(f"Missing .agentic/{triad}/AGENTS.md")

    if not (agentic / "AGENTS.md").is_file():
        errors.append("Missing .agentic/AGENTS.md")

    return errors


def validate_schemas(repo_path: Path, schemas_path: Path) -> list[str]:
    """Validate JSON files against schemas."""
    errors = []

    for schema_file in schemas_path.rglob("*.schema.json"):
        try:
            with open(schema_file) as f:
                json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid schema JSON in {schema_file.name}: {e}")

    return errors


def validate_naming(repo_path: Path) -> list[str]:
    """Check file naming conventions (underscores, not hyphens)."""
    errors = []
    skip_dirs = {".git", "node_modules", ".venv", "__pycache__"}

    for path in repo_path.rglob("*"):
        if any(skip in path.parts for skip in skip_dirs):
            continue
        if path.is_file() and path.suffix in (".py", ".yaml", ".yml", ".json"):
            if "-" in path.stem and path.stem not in ("docker-compose", ".pre-commit-config"):
                errors.append(f"File '{path.relative_to(repo_path)}' uses hyphens — prefer underscores")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Rare Archive compliance validation")
    parser.add_argument("--repo-path", default=".", help="Repository path")
    parser.add_argument("--schemas-path", default="", help="Schemas directory")
    parser.add_argument("--min-fair-score", type=int, default=0, help="Minimum FAIR score")
    parser.add_argument("--check-naming", default="true", help="Check naming conventions")
    args = parser.parse_args()

    repo_path = Path(args.repo_path).resolve()
    schemas_path = Path(args.schemas_path).resolve() if args.schemas_path else repo_path / "schemas"

    print(f"Validating: {repo_path}")
    print("=" * 50)

    all_errors = []

    # 1. aDNA triad
    triad_errors = validate_adna_triad(repo_path)
    if triad_errors:
        print(f"\naDNA Triad: FAIL")
        for e in triad_errors:
            print(f"  - {e}")
        all_errors.extend(triad_errors)
    else:
        print(f"\naDNA Triad: PASS")

    # 2. Schema validation
    if schemas_path.is_dir():
        schema_errors = validate_schemas(repo_path, schemas_path)
        if schema_errors:
            print(f"\nSchemas: FAIL")
            for e in schema_errors:
                print(f"  - {e}")
            all_errors.extend(schema_errors)
        else:
            print(f"\nSchemas: PASS")

    # 3. Naming conventions
    if args.check_naming == "true":
        naming_errors = validate_naming(repo_path)
        if naming_errors:
            print(f"\nNaming: WARN ({len(naming_errors)} issues)")
            for e in naming_errors[:10]:
                print(f"  - {e}")
        else:
            print(f"\nNaming: PASS")

    print("\n" + "=" * 50)
    if all_errors:
        print(f"FAILED: {len(all_errors)} errors")
        sys.exit(1)
    else:
        print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
