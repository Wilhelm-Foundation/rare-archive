"""Tests for evaluation submission endpoints."""


class TestSubmitEvaluation:
    """Tests for POST /evaluations/submit."""

    async def test_creates_evaluation(self, client, sample_expert):
        resp = await client.post("/evaluations/submit", json={
            "expert_username": "dr_smith",
            "case_id": "CASE002",
            "model_a_id": "model-X",
            "model_b_id": "model-Y",
            "model_a_response": "Response X",
            "model_b_response": "Response Y",
            "winner": "b",
            "model_a_annotations": {
                "diagnostic_accuracy": 2, "reasoning_quality": 2,
                "tool_usage": 2, "safety": 2,
            },
            "model_b_annotations": {
                "diagnostic_accuracy": 4, "reasoning_quality": 4,
                "tool_usage": 4, "safety": 4,
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["case_id"] == "CASE002"
        assert data["winner"] == "b"

    async def test_triggers_elo_update(self, client, sample_expert):
        resp = await client.post("/evaluations/submit", json={
            "expert_username": "dr_smith",
            "case_id": "CASE003",
            "model_a_id": "model-P",
            "model_b_id": "model-Q",
            "model_a_response": "Response P",
            "model_b_response": "Response Q",
            "winner": "a",
            "model_a_annotations": {
                "diagnostic_accuracy": 3, "reasoning_quality": 3,
                "tool_usage": 3, "safety": 3,
            },
            "model_b_annotations": {
                "diagnostic_accuracy": 1, "reasoning_quality": 1,
                "tool_usage": 1, "safety": 1,
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "elo_update" in data
        assert data["elo_update"]["status"] == "updated"

    async def test_invalid_expert_404(self, client):
        resp = await client.post("/evaluations/submit", json={
            "expert_username": "nonexistent",
            "case_id": "CASE001",
            "model_a_id": "A",
            "model_b_id": "B",
            "model_a_response": "A",
            "model_b_response": "B",
            "winner": "a",
            "model_a_annotations": {
                "diagnostic_accuracy": 1, "reasoning_quality": 1,
                "tool_usage": 1, "safety": 1,
            },
            "model_b_annotations": {
                "diagnostic_accuracy": 1, "reasoning_quality": 1,
                "tool_usage": 1, "safety": 1,
            },
        })
        assert resp.status_code == 404


class TestGetStats:
    """Tests for GET /evaluations/stats."""

    async def test_total_count(self, client, sample_evaluation):
        resp = await client.get("/evaluations/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_evaluations"] >= 1

    async def test_per_category_breakdown(self, client, sample_evaluation):
        resp = await client.get("/evaluations/stats")
        data = resp.json()
        assert "neuromuscular" in data["by_category"]
        assert data["by_category"]["neuromuscular"] >= 1
