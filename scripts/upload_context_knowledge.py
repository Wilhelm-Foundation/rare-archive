#!/usr/bin/env python3
"""Upload context YAML files to OpenWebUI Knowledge Base.

Converts rare disease diagnostic context files (YAML) to structured Markdown,
creates a Knowledge Base in OpenWebUI, and uploads the converted files.

Usage:
    python3 scripts/upload_context_knowledge.py <openwebui_url> <api_key> [--kb-name NAME] [--dry-run]

Examples:
    # Dry run — convert and print Markdown, no upload
    python3 scripts/upload_context_knowledge.py http://localhost:3100 dummy --dry-run

    # Upload to L2 OpenWebUI
    python3 scripts/upload_context_knowledge.py http://localhost:3100 sk-abc123
"""

import argparse
import io
import sys
from pathlib import Path

import httpx
import yaml

CONTEXT_DIR = Path(__file__).parent.parent / "packages" / "ontology" / "context"
CONTEXT_FILES = [
    "rare_ctx_workflow_lsd_gaucher.yaml",
    "rare_ctx_datasource_nanopore_longread.yaml",
]

DEFAULT_KB_NAME = "Rare Disease Diagnostic Context"


def yaml_to_markdown(yaml_path: Path) -> str:
    """Convert a context YAML file to structured Markdown for RAG chunking.

    Uses H2/H3 headers so OpenWebUI's text splitter creates meaningful chunks
    (each workflow step, interpretation note, etc. becomes its own retrievable unit).
    """
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    lines: list[str] = []

    # Title and description
    lines.append(f"# {data.get('title', yaml_path.stem)}")
    lines.append("")
    if desc := data.get("description"):
        lines.append(desc)
        lines.append("")

    # When to use
    if wtu := data.get("when_to_use"):
        lines.append("## When to Use")
        lines.append("")
        if features := wtu.get("presenting_features"):
            lines.append("**Presenting features:**")
            for feat in features:
                lines.append(f"- {feat}")
            lines.append("")
        if ctx := wtu.get("patient_context"):
            lines.append(f"**Patient context:** {ctx}")
            lines.append("")
        if trigger := wtu.get("trigger_condition"):
            lines.append(f"**Trigger condition:** {trigger}")
            lines.append("")
        if prereqs := wtu.get("prerequisites"):
            lines.append("**Prerequisites:**")
            for p in prereqs:
                lines.append(f"- {p}")
            lines.append("")

    # Disease associations
    if diseases := data.get("disease_associations"):
        lines.append("## Disease Associations")
        lines.append("")
        for d in diseases:
            name = d.get("name", "Unknown")
            relevance = d.get("relevance", "")
            ids = []
            if omim := d.get("omim_id"):
                ids.append(f"OMIM:{omim}")
            if orpha := d.get("orpha_id"):
                ids.append(orpha)
            if mondo := d.get("mondo_id"):
                ids.append(mondo)
            id_str = f" ({', '.join(ids)})" if ids else ""
            lines.append(f"- **{name}**{id_str} — {relevance}")
        lines.append("")

    # Tool connections
    if tools := data.get("tool_connections"):
        lines.append("## Tool Connections")
        lines.append("")
        for t in tools:
            lines.append(f"- **{t.get('tool_id', '')}**: {t.get('role', '')}")
        lines.append("")

    # Workflow steps
    if steps := data.get("workflow_steps"):
        lines.append("## Diagnostic Workflow")
        lines.append("")
        for step in steps:
            num = step.get("step", "?")
            action = step.get("action", "")
            lines.append(f"### Step {num}: {action}")
            lines.append("")
            if tool := step.get("tool_id"):
                lines.append(f"**Tool:** {tool}")
                lines.append("")
            if reasoning := step.get("reasoning"):
                lines.append(reasoning)
                lines.append("")
            if expected := step.get("expected_output"):
                lines.append(f"**Expected output:** {expected}")
                lines.append("")
            if branch := step.get("decision_branch"):
                lines.append("**Decision branches:**")
                if pos := branch.get("if_positive"):
                    lines.append(f"- If positive: {pos}")
                if neg := branch.get("if_negative"):
                    lines.append(f"- If negative: {neg}")
                if amb := branch.get("if_ambiguous"):
                    lines.append(f"- If ambiguous: {amb}")
                lines.append("")

    # Interpretation notes
    if notes := data.get("interpretation_notes"):
        lines.append("## Interpretation Notes")
        lines.append("")
        for note in notes:
            ctx = note.get("context", "")
            lines.append(f"### {ctx}")
            lines.append("")
            if guidance := note.get("guidance"):
                lines.append(guidance)
                lines.append("")

    # Confidence assessment
    if conf := data.get("confidence_assessment"):
        lines.append("## Confidence Assessment")
        lines.append("")
        if overall := conf.get("overall"):
            lines.append(f"**Overall confidence:** {overall}")
            lines.append("")
        if factors := conf.get("limiting_factors"):
            lines.append("**Limiting factors:**")
            for f in factors:
                lines.append(f"- {f}")
            lines.append("")
        if alts := conf.get("alternative_differentials"):
            lines.append("**Alternative differentials:**")
            for a in alts:
                lines.append(f"- {a}")
            lines.append("")

    # Examples
    if examples := data.get("examples"):
        lines.append("## Clinical Examples")
        lines.append("")
        for i, ex in enumerate(examples, 1):
            lines.append(f"### Example {i}")
            lines.append("")
            if scenario := ex.get("scenario"):
                lines.append(f"**Scenario:** {scenario}")
                lines.append("")
            if behavior := ex.get("expected_behavior"):
                lines.append(f"**Expected behavior:** {behavior}")
                lines.append("")
            if seq := ex.get("tool_sequence"):
                lines.append(f"**Tool sequence:** {' -> '.join(seq)}")
                lines.append("")

    return "\n".join(lines)


def create_or_get_kb(client: httpx.Client, base_url: str, name: str, description: str = "") -> str:
    """Create a Knowledge Base or return existing one if name matches."""
    # List existing KBs
    resp = client.get(f"{base_url}/api/v1/knowledge/")
    resp.raise_for_status()
    existing = resp.json()

    # Check for existing KB with same name
    # API may return a list or a paginated dict with "items" key
    items = existing.get("items", existing) if isinstance(existing, dict) else existing
    for kb in items:
        if kb.get("name") == name:
            print(f"  Found existing KB: {kb['id']} ({name})")
            return kb["id"]

    # Create new KB
    resp = client.post(
        f"{base_url}/api/v1/knowledge/create",
        json={
            "name": name,
            "description": description or f"Diagnostic context files for rare disease AI",
        },
    )
    resp.raise_for_status()
    kb = resp.json()
    print(f"  Created KB: {kb['id']} ({name})")
    return kb["id"]


def upload_file(client: httpx.Client, base_url: str, kb_id: str, filename: str, content: str) -> str:
    """Upload a Markdown file to a Knowledge Base."""
    # Upload file
    file_bytes = content.encode("utf-8")
    resp = client.post(
        f"{base_url}/api/v1/files/",
        files={"file": (filename, io.BytesIO(file_bytes), "text/markdown")},
    )
    resp.raise_for_status()
    file_data = resp.json()
    file_id = file_data["id"]
    print(f"  Uploaded file: {file_id} ({filename})")

    # Associate file with KB
    resp = client.post(
        f"{base_url}/api/v1/knowledge/{kb_id}/file/add",
        json={"file_id": file_id},
    )
    resp.raise_for_status()
    print(f"  Associated with KB: {kb_id}")

    return file_id


def main():
    parser = argparse.ArgumentParser(
        description="Upload context YAML files to OpenWebUI Knowledge Base"
    )
    parser.add_argument("openwebui_url", help="OpenWebUI base URL (e.g. http://localhost:3100)")
    parser.add_argument("api_key", help="OpenWebUI API key (Bearer token)")
    parser.add_argument("--kb-name", default=DEFAULT_KB_NAME, help="Knowledge Base name")
    parser.add_argument("--dry-run", action="store_true", help="Convert and print Markdown only, no upload")
    args = parser.parse_args()

    print("=" * 60)
    print("  Rare AI Archive — Context Knowledge Upload")
    print("=" * 60)

    # Convert all YAML files
    converted: list[tuple[str, str]] = []  # (filename, markdown)
    for yaml_name in CONTEXT_FILES:
        yaml_path = CONTEXT_DIR / yaml_name
        if not yaml_path.exists():
            print(f"\n  SKIP  {yaml_name} — file not found")
            continue

        md_content = yaml_to_markdown(yaml_path)
        md_name = yaml_path.stem + ".md"
        converted.append((md_name, md_content))
        print(f"\n  OK    {yaml_name} -> {md_name} ({len(md_content)} chars)")

    if args.dry_run:
        print(f"\n{'─' * 60}")
        print("  DRY RUN — Markdown output:")
        for md_name, md_content in converted:
            print(f"\n{'=' * 40}")
            print(f"  {md_name}")
            print(f"{'=' * 40}")
            print(md_content)
        print(f"\n{'=' * 60}")
        print(f"  {len(converted)} files converted (dry run, no upload)")
        print(f"{'=' * 60}")
        return

    if not converted:
        print("\n  No files to upload.")
        sys.exit(1)

    # Upload to OpenWebUI
    client = httpx.Client(
        headers={"Authorization": f"Bearer {args.api_key}"},
        timeout=60,
    )

    try:
        print(f"\n  Connecting to {args.openwebui_url}...")
        kb_id = create_or_get_kb(client, args.openwebui_url, args.kb_name)

        uploaded = 0
        for md_name, md_content in converted:
            try:
                upload_file(client, args.openwebui_url, kb_id, md_name, md_content)
                uploaded += 1
            except Exception as e:
                print(f"  ERROR uploading {md_name}: {e}")

        print(f"\n{'=' * 60}")
        print(f"  Results: {uploaded}/{len(converted)} files uploaded to KB '{args.kb_name}'")
        print(f"  KB ID: {kb_id}")
        print(f"\n  Next steps:")
        print(f"    1. Go to OpenWebUI Settings -> Models -> qwen3.5-35b-a3b")
        print(f"    2. Under Knowledge, attach '{args.kb_name}'")
        print(f"    3. Test: Ask about Gaucher disease in an Ashkenazi patient")
        print(f"{'=' * 60}")

    finally:
        client.close()

    sys.exit(0 if uploaded == len(converted) else 1)


if __name__ == "__main__":
    main()
