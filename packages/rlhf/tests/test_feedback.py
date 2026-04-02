"""Tests for clinical feedback endpoints — corrections, annotations, tool quality."""

import pytest


class TestToolQuality:
    """Tests for POST /feedback/tool-quality."""

    async def test_submit_tool_quality(self, client, sample_expert):
        resp = await client.post("/feedback/tool-quality", json={
            "expert_username": "dr_smith",
            "case_id": "CASE001",
            "tool_name": "orphanet",
            "quality_score": 4,
            "was_appropriate": True,
            "was_missing": False,
            "reasoning": "Correct tool for rare disease lookup",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["feedback_type"] == "tool_quality"
        assert data["structured_data"]["tool_name"] == "orphanet"
        assert data["structured_data"]["quality_score"] == 4
        assert data["structured_data"]["was_appropriate"] is True
        assert data["structured_data"]["was_missing"] is False
        assert data["text"] == "Correct tool for rare disease lookup"

    async def test_tool_quality_requires_valid_score(self, client, sample_expert):
        resp = await client.post("/feedback/tool-quality", json={
            "expert_username": "dr_smith",
            "tool_name": "clinvar",
            "quality_score": 6,
            "was_appropriate": True,
            "was_missing": False,
            "reasoning": "Invalid score",
        })
        assert resp.status_code == 422  # Pydantic validation error

    async def test_tool_quality_negative_score_rejected(self, client, sample_expert):
        resp = await client.post("/feedback/tool-quality", json={
            "expert_username": "dr_smith",
            "tool_name": "clinvar",
            "quality_score": -1,
            "was_appropriate": True,
            "was_missing": False,
            "reasoning": "Negative score",
        })
        assert resp.status_code == 422

    async def test_tool_quality_in_stats(self, client, sample_expert):
        await client.post("/feedback/tool-quality", json={
            "expert_username": "dr_smith",
            "tool_name": "hpo",
            "quality_score": 2,
            "was_appropriate": False,
            "was_missing": False,
            "reasoning": "HPO endpoint was deprecated",
        })
        resp = await client.get("/feedback/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "tool_quality" in data["by_type"]
        assert data["by_type"]["tool_quality"] >= 1


class TestAnnotation:
    """Tests for POST /feedback/annotation with tool_quality type."""

    async def test_annotation_accepts_tool_quality_type(self, client, sample_expert):
        resp = await client.post("/feedback/annotation", json={
            "expert_username": "dr_smith",
            "feedback_type": "tool_quality",
            "text": "Orphanet tool was excellent",
        })
        assert resp.status_code == 200
        assert resp.json()["feedback_type"] == "tool_quality"
