#!/usr/bin/env bash
# run_e2e.sh — Run Playwright E2E tests against OpenWebUI on L2.
#
# Prerequisites:
#   1. SSH tunnel to L2 forwarding port 3100
#   2. Environment variables: RARE_ARCHIVE_OPENWEBUI_USER, RARE_ARCHIVE_OPENWEBUI_PASS
#   3. pip install -r requirements-e2e.txt && playwright install chromium
#
# Usage:
#   ./scripts/run_e2e.sh                  # all 5 scenarios
#   ./scripts/run_e2e.sh -k "gaucher"     # single scenario

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ── Preflight checks ────────────────────────────────────────────────────────

# Check env vars
if [[ -z "${RARE_ARCHIVE_OPENWEBUI_USER:-}" ]] || [[ -z "${RARE_ARCHIVE_OPENWEBUI_PASS:-}" ]]; then
    echo "ERROR: Set RARE_ARCHIVE_OPENWEBUI_USER and RARE_ARCHIVE_OPENWEBUI_PASS"
    exit 1
fi

# Check tunnel (default port 3100)
OWUI_URL="${RARE_ARCHIVE_OPENWEBUI_URL:-http://localhost:3100}"
OWUI_HOST=$(echo "$OWUI_URL" | sed -E 's|https?://||' | cut -d/ -f1)

if ! nc -z "${OWUI_HOST%%:*}" "${OWUI_HOST##*:}" 2>/dev/null; then
    echo "ERROR: Cannot reach $OWUI_URL — is the SSH tunnel running?"
    echo "  ssh -L 3100:localhost:3100 <l2-host>"
    exit 1
fi

echo "✓ OpenWebUI reachable at $OWUI_URL"
echo "✓ Credentials set"
echo ""

# ── Run tests ────────────────────────────────────────────────────────────────

cd "$REPO_ROOT"
exec pytest tests/e2e/ -m e2e -v --timeout=120 "$@"
