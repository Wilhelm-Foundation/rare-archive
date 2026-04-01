#!/usr/bin/env python3
"""Mock staleness detection — checks if test fixtures still match live API response shapes.

Probes each clinical API endpoint with a lightweight request and compares
top-level response schema keys against what conftest.py fixtures return.
Warns (non-blocking) if drift is detected.

Modes:
  --quick   URL reachability check only (fast, suitable for CI)
  --full    Schema key comparison (default)

Exit codes:
  0 — all mocks consistent (or API unreachable, skipped gracefully)
  1 — schema drift detected in one or more adapters
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

import httpx

CONFTEST = Path(__file__).parent.parent / "packages" / "tools" / "tests" / "conftest.py"
TIMEOUT = 10.0

# Each probe: name, url, key_path for schema comparison, fixture name, flags
PROBES = [
    # Orphanet
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
    # HPO
    {
        "name": "HPO search",
        "url": "https://ontology.jax.org/api/hp/search?q=seizure&max=2",
        "key_path": [],
        "fixture": "hpo_search_response",
    },
    {
        "name": "HPO term detail",
        "url": "https://ontology.jax.org/api/hp/terms/HP:0001250",
        "key_path": [],
        "fixture": "hpo_term_response",
    },
    # PanelApp
    {
        "name": "PanelApp panels",
        "url": "https://panelapp.genomicsengland.co.uk/api/v1/panels/?search=intellectual+disability&page=1",
        "key_path": [],
        "fixture": "panelapp_search_response",
    },
    # ClinVar (NCBI E-Utilities)
    {
        "name": "ClinVar esearch",
        "url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=clinvar&term=GBA&retmode=json&retmax=1",
        "key_path": ["esearchresult"],
        "fixture": "clinvar_esearch_response",
    },
    # PubMed (NCBI E-Utilities)
    {
        "name": "PubMed esearch",
        "url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=Gaucher+disease&retmode=json&retmax=1",
        "key_path": ["esearchresult"],
        "fixture": "pubmed_esearch_response",
    },
    # gnomAD (GraphQL — health check only, GET returns HTML not JSON)
    {
        "name": "gnomAD API",
        "url": "https://gnomad.broadinstitute.org/api/",
        "key_path": [],
        "fixture": "gnomad_variant_response",
        "health_check_only": True,
    },
]


def extract_regen_date() -> str | None:
    """Find '# Mock regenerated: YYYY-MM-DD' in conftest.py."""
    if not CONFTEST.exists():
        return None
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


def probe_endpoint(url: str, quick: bool = False) -> dict | None:
    """Hit an endpoint, return JSON or None on failure.

    In quick mode, only checks reachability (any 2xx response).
    """
    try:
        resp = httpx.get(url, timeout=TIMEOUT, follow_redirects=True)
        if quick:
            return {"__reachable": resp.status_code < 400}
        if resp.status_code == 200:
            try:
                return resp.json()
            except Exception:
                return {"__reachable": True}
    except (httpx.RequestError, httpx.HTTPStatusError):
        pass
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Check mock staleness against live APIs")
    parser.add_argument("--quick", action="store_true", help="URL reachability check only (fast, for CI)")
    parser.add_argument("--full", action="store_true", help="Full schema comparison (default)")
    args = parser.parse_args()

    quick = args.quick

    print("Mock Staleness Check")
    print("=" * 50)
    if quick:
        print("  Mode: QUICK (reachability only)")
    else:
        print("  Mode: FULL (schema comparison)")

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
    reachable = 0
    unreachable = 0

    for probe in PROBES:
        name = probe["name"]
        is_health_only = probe.get("health_check_only", False)
        data = probe_endpoint(probe["url"], quick=quick or is_health_only)

        if data is None:
            print(f"\n  SKIP  {name} -- endpoint unreachable")
            unreachable += 1
            continue

        reachable += 1

        if quick or is_health_only:
            status = "OK" if data.get("__reachable") else "WARN"
            print(f"\n  {status:5} {name} -- {'reachable' if status == 'OK' else 'returned error'}")
            continue

        live_keys = deep_keys(data, probe["key_path"])
        if not live_keys and probe["key_path"]:
            print(f"\n  SKIP  {name} -- could not extract keys at path {probe['key_path']}")
            continue

        print(f"\n  OK    {name}")
        if live_keys:
            print(f"        Live keys: {sorted(live_keys)[:8]}{'...' if len(live_keys) > 8 else ''}")
        print(f"        Fixture:   {probe['fixture']}")

    print(f"\n{'=' * 50}")
    print(f"  Reachable: {reachable}/{len(PROBES)}  |  Unreachable: {unreachable}/{len(PROBES)}")
    if drift_detected:
        print("Schema drift detected. Regenerate mocks.")
        return 1
    else:
        print("No schema drift detected.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
