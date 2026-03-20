"""Tests for preference pair extraction and export."""


class TestGetPairs:
    """Tests for GET /preferences/pairs."""

    async def test_returns_dpo_format(self, client, sample_evaluation):
        resp = await client.get("/preferences/pairs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        pair = data["pairs"][0]
        assert "prompt" in pair
        assert "chosen" in pair
        assert "rejected" in pair

    async def test_ties_excluded(self, client, sample_expert):
        await client.post("/evaluations/submit", json={
            "expert_username": "dr_smith",
            "case_id": "TIE_CASE",
            "model_a_id": "A",
            "model_b_id": "B",
            "model_a_response": "Same quality",
            "model_b_response": "Same quality",
            "winner": "tie",
            "model_a_annotations": {
                "diagnostic_accuracy": 3, "reasoning_quality": 3,
                "tool_usage": 3, "safety": 3,
            },
            "model_b_annotations": {
                "diagnostic_accuracy": 3, "reasoning_quality": 3,
                "tool_usage": 3, "safety": 3,
            },
        })
        resp = await client.get("/preferences/pairs")
        data = resp.json()
        assert data["count"] == 0

    async def test_category_filter(self, client, sample_evaluation):
        resp = await client.get(
            "/preferences/pairs",
            params={"patient_category": "neuromuscular"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1


class TestExport:
    """Tests for POST /preferences/export."""

    async def test_creates_export_record(self, client, sample_evaluation):
        resp = await client.post("/preferences/export")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["pairs_exported"] >= 1

    async def test_no_data_handled(self, client):
        resp = await client.post("/preferences/export")
        assert resp.status_code == 200
        assert resp.json()["status"] == "no_data"
