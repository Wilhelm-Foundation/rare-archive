#!/usr/bin/env bash
# Rare AI Archive — Development Setup
# Installs all packages in editable mode for local development

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "╔══════════════════════════════════════════════════╗"
echo "║       Rare AI Archive — Development Setup        ║"
echo "║                                                  ║"
echo "║  300 million people live with rare diseases.     ║"
echo "║  Diagnostic odysseys average 5-7 years.          ║"
echo "║  We're building the tools to change that.        ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

PACKAGES=(
    "packages/ontology"
    "packages/compliance"
    "packages/datasets"
    "packages/models"
    "packages/tools"
    "packages/rlhf"
)

echo "Installing ${#PACKAGES[@]} packages in development mode..."
echo ""

for pkg in "${PACKAGES[@]}"; do
    pkg_path="${REPO_ROOT}/${pkg}"
    if [ -f "${pkg_path}/pyproject.toml" ]; then
        echo "  [install] ${pkg}"
        pip install -e "${pkg_path}" 2>/dev/null || echo "  [warn] ${pkg} — pip install failed"
    else
        echo "  [skip] ${pkg} — no pyproject.toml"
    fi
done

echo ""
echo "Done. All packages installed in editable mode."
echo "See README.md for architecture overview."
