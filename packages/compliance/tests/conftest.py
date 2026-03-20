"""Shared fixtures for compliance package tests."""

import pytest


@pytest.fixture
def valid_envelope():
    """Minimal valid aDNA envelope."""
    return {
        "name": "test_artifact",
        "version": "1.0.0",
        "type": "rare_model",
        "namespace": "rare_",
        "triad": "what",
        "created": "2025-01-01",
        "updated": "2025-01-15",
        "last_edited_by": "agent:test",
    }


@pytest.fixture
def adna_triad_repo(tmp_path):
    """Create a valid aDNA triad directory structure in tmp_path."""
    agentic = tmp_path / ".agentic"
    agentic.mkdir()
    (agentic / "AGENTS.md").write_text("# Agents")
    for leg in ("what", "how", "who"):
        d = agentic / leg
        d.mkdir()
        (d / "AGENTS.md").write_text(f"# {leg}")
    return tmp_path


@pytest.fixture
def fully_compliant_metadata():
    """Metadata that passes all FAIR criteria for a non-dataset, non-model artifact."""
    return {
        "name": "test_tool",
        "description": "A fully compliant clinical tool for testing purposes",
        "version": "1.0.0",
        "persistent_id": "doi:10.1234/test",
        "license": "Apache-2.0",
        "creators": [{"name": "Test Author"}],
        "keywords": ["rare-disease", "clinical", "diagnostic"],
        "references": ["doi:10.1234/ref1"],
        "category_id": "rare_cat_neuromuscular",
        "adna": {
            "type": "rare_clinical_tool",
            "namespace": "rare_",
            "triad": "what",
        },
    }


@pytest.fixture
def minimal_metadata():
    """Metadata with only a name — fails most FAIR criteria."""
    return {"name": "bare_artifact"}
