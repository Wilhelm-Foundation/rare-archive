#!/usr/bin/env python3
"""Register clinical tools with OpenWebUI.

M04 Phase C — reads each OpenWebUI tool wrapper and POSTs it
to the OpenWebUI API for registration.

Usage:
    python3 scripts/register_openwebui_tools.py <jwt_token>
"""

import json
import re
import sys
from pathlib import Path

import httpx

OPENWEBUI_URL = "http://localhost:3100"
TOOLS_DIR = Path("packages/tools/src/rare_archive_tools/openwebui")

TOOLS = [
    {"id": "clinvar_lookup",  "file": "clinvar_tool.py",         "name": "ClinVar Variant Lookup"},
    {"id": "orphanet_search", "file": "orphanet_tool.py",        "name": "Orphanet Disease Search"},
    {"id": "hpo_lookup",      "file": "hpo_tool.py",             "name": "HPO Phenotype Lookup"},
    {"id": "panelapp_search", "file": "panelapp_tool.py",        "name": "PanelApp Gene Panel Query"},
    {"id": "gnomad_lookup",   "file": "gnomad_tool.py",          "name": "gnomAD Allele Frequency"},
    {"id": "pubmed_search",   "file": "pubmed_tool.py",          "name": "PubMed Literature Search"},
    {"id": "differential_dx", "file": "differential_dx_tool.py", "name": "Differential Diagnosis"},
]


def extract_description(content: str) -> str:
    """Extract description from tool file docstring metadata."""
    match = re.search(r'description:\s*(.+)', content)
    return match.group(1).strip() if match else ""


def register_tool(client: httpx.Client, tool_id: str, name: str, content: str, description: str) -> dict:
    """Register a single tool with OpenWebUI."""
    # First try to delete if exists (idempotent)
    client.delete(f"{OPENWEBUI_URL}/api/v1/tools/id/{tool_id}/delete")

    resp = client.post(
        f"{OPENWEBUI_URL}/api/v1/tools/create",
        json={
            "id": tool_id,
            "name": name,
            "content": content,
            "meta": {"description": description},
        },
    )
    resp.raise_for_status()
    return resp.json()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 register_openwebui_tools.py <jwt_token>")
        sys.exit(1)

    token = sys.argv[1]
    client = httpx.Client(headers={"Authorization": f"Bearer {token}"}, timeout=30)

    print("=" * 60)
    print("  Rare AI Archive — OpenWebUI Tool Registration (M04 Phase C)")
    print("=" * 60)

    registered = 0
    for tool in TOOLS:
        tool_path = TOOLS_DIR / tool["file"]
        if not tool_path.exists():
            print(f"  ✗ MISSING — {tool['file']}")
            continue

        content = tool_path.read_text()
        description = extract_description(content)

        try:
            result = register_tool(client, tool["id"], tool["name"], content, description)
            print(f"  ✓ {tool['id']} — {tool['name']}")
            registered += 1
        except Exception as e:
            print(f"  ✗ {tool['id']} — {e}")

    # Verify
    print(f"\n{'─' * 40}")
    resp = client.get(f"{OPENWEBUI_URL}/api/v1/tools/")
    tools = resp.json()
    tool_ids = [t["id"] for t in tools]
    print(f"  Registered tools: {tool_ids}")
    print(f"\n{'=' * 60}")
    print(f"  Results: {registered}/{len(TOOLS)} tools registered")
    print(f"{'=' * 60}")

    client.close()
    sys.exit(0 if registered == len(TOOLS) else 1)


if __name__ == "__main__":
    main()
