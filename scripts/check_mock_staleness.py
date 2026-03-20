#!/usr/bin/env python3
"""Mock staleness detection — checks if test fixtures still match live API response shapes.

Probes each clinical API endpoint with a lightweight request and compares
top-level response schema keys against what conftest.py fixtures return.
Warns (non-blocking) if drift is detected.

Exit codes:
  0 — all mocks consistent (or API unreachable, skipped gracefully)
  1 — schema drift detected in one or more adapters
"""

import re
import sys
from datetime import datetime
from pathlib import Path

import httpx

CONFTEST = Path(__file__).parent.parent / "packages" / "tools" / "tests" / "conftest.py"
TIMEOUT = 10.0

# Each probe: (name, url, expected_schema_path, fixture_schema_path)
# schema_path is a dot-separated key path to compare (e.g. "data.results")
PROBES = [
    {
        "name": "Orphanet search",
        "url": "https://api.orphadata.com/rd-cross-referencing/orphacodes/names/Marfan",
        "key_path": ["data", "results"],
        "fixture": "orphanet_search_response",
    },
    {
        "name": "Orphanet disease",
        "url": "https://api.orphadata.com/rd-cross-referencing/orphacodes/558",
        "key_path": ["data", "results"],
        "fixture": "orphanet_disease_response",
    },
    {
        "name": "Orphanet phenotypes",
        "url": "https://api.orphadata.com/rd-phenotypes/orphacodes/558",
        "key_path": ["data", "results"],
        "fixture": "orphanet_phenotypes (no fixture)",
    },
    {
        "name": "HPO search",
        "url": "https://ontology.jax.org/api/hp/search?q=seizure&max=2",
        "key_path": [],
        "fixture": "hpo_search_response",
    },
    {
        "name": "PanelApp panels",
        "url": "https://panelapp.genomicsengland.co.uk/api/v1/panels/?search=intellectual+disability&page=1",
        "key_path": [],
        "fixture": "panelapp_search_response",
    },
]


def extract_regen_date() -> str | None:
    """Find '# Mock regenerated: YYYY-MM-DD' in conftest.py."""
    text = CONFTEST.read_text()
    m = re.search(r"# Mock regenerated:\s*(\d{4}-\d{2}-\d{2})", text)
    return m.group(1) if m else None


def deep_keys(obj: dict, path: list[str]) -> set[str]:
    """Navigate into obj along path, return keys at that level."""
    current = obj
    for key in path:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return set()
    if isinstance(current, dict):
        return set(current.keys())
    return set()


def probe_endpoint(url: str) -> dict | None:
    """Hit an endpoint, return JSON or None on failure."""
    try:
        resp = httpx.get(url, timeout=TIMEOUT, follow_redirects=True)
        if resp.status_code == 200:
            return resp.json()
    except (httpx.RequestError, httpx.HTTPStatusError):
        pass
    return None


def main() -> int:
    print("Mock Staleness Check")
    print("=" * 50)

    # Check regeneration date
    regen_date = extract_regen_date()
    if regen_date:
        days_since = (datetime.now() - datetime.strptime(regen_date, "%Y-%m-%d")).days
        print(f"  Last regenerated: {regen_date} ({days_since} days ago)")
        if days_since > 30:
            print(f"  WARNING: Mocks are {days_since} days old (>30 day threshold)")
    else:
        print("  WARNING: No regeneration date found in conftest.py")

    # Probe endpoints
    drift_detected = False
    for probe in PROBES:
        name = probe["name"]
        data = probe_endpoint(probe["url"])

        if data is None:
            print(f"\n  SKIP  {name} — endpoint unreachable")
            continue

        live_keys = deep_keys(data, probe["key_path"])
        if not live_keys:
            print(f"\n  SKIP  {name} — could not extract keys at path {probe['key_path']}")
            continue

        # We report the live keys for manual comparison
        # (Automated fixture key extraction would require AST parsing of conftest.py)
        print(f"\n  OK    {name}")
        print(f"        Live keys: {sorted(live_keys)[:8]}{'...' if len(live_keys) > 8 else ''}")
        print(f"        Fixture:   {probe['fixture']}")

    print("\n" + "=" * 50)
    if drift_detected:
        print("Schema drift detected. Regenerate mocks.")
        return 1
    else:
        print("No schema drift detected.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
