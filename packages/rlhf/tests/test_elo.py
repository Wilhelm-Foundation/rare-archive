"""Tests for ELO rating endpoints and computation."""

from archive_api.routers.elo import _compute_elo_change


class TestComputeEloChange:
    """Tests for the pure _compute_elo_change function."""

    def test_higher_rated_wins_small_gain(self):
        new_a, new_b = _compute_elo_change(1600, 1400, 1.0, 32)
        assert new_a > 1600
        assert new_b < 1400
        gain = new_a - 1600
        assert gain < 16  # Expected outcome → small gain

    def test_upset_win_large_gain(self):
        new_a, new_b = _compute_elo_change(1400, 1600, 1.0, 32)
        gain = new_a - 1400
        assert gain > 16  # Unexpected outcome → large gain

    def test_tie_ratings_converge(self):
        new_a, new_b = _compute_elo_change(1600, 1400, 0.5, 32)
        assert new_a < 1600  # Higher-rated drops
        assert new_b > 1400  # Lower-rated rises

    def test_k_factor_scales_changes(self):
        new_a_small, _ = _compute_elo_change(1500, 1500, 1.0, 16)
        new_a_large, _ = _compute_elo_change(1500, 1500, 1.0, 64)
        assert abs(new_a_large - 1500) > abs(new_a_small - 1500)


class TestGetRatings:
    """Tests for GET /elo/ratings."""

    async def test_returns_sorted_by_elo(self, client):
        await client.post("/elo/update", json={
            "winner_model_id": "model-A",
            "loser_model_id": "model-B",
        })
        resp = await client.get("/elo/ratings")
        assert resp.status_code == 200
        ratings = resp.json()
        assert len(ratings) == 2
        assert ratings[0]["overall_elo"] >= ratings[1]["overall_elo"]

    async def test_category_filter(self, client):
        await client.post("/elo/update", json={
            "winner_model_id": "model-A",
            "loser_model_id": "model-B",
            "patient_category": "neuro",
        })
        await client.post("/elo/update", json={
            "winner_model_id": "model-C",
            "loser_model_id": "model-D",
            "patient_category": "metabolic",
        })
        resp = await client.get("/elo/ratings", params={"patient_category": "neuro"})
        assert resp.status_code == 200
        ratings = resp.json()
        assert all(r["patient_category"] == "neuro" for r in ratings)


class TestPostUpdate:
    """Tests for POST /elo/update."""

    async def test_win_updates_ratings(self, client):
        resp = await client.post("/elo/update", json={
            "winner_model_id": "model-A",
            "loser_model_id": "model-B",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "updated"
        assert data["winner"]["new_elo"] > 1500
        assert data["loser"]["new_elo"] < 1500

    async def test_tie_keeps_ratings_close(self, client):
        resp = await client.post("/elo/update", json={
            "winner_model_id": "model-A",
            "loser_model_id": "model-B",
            "is_tie": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert abs(data["winner"]["new_elo"] - 1500) < 1
        assert abs(data["loser"]["new_elo"] - 1500) < 1

    async def test_dimensional_elo_with_annotations(self, client):
        resp = await client.post("/elo/update", json={
            "winner_model_id": "model-A",
            "loser_model_id": "model-B",
            "annotations": {
                "winner_diagnostic_accuracy": 5,
                "loser_diagnostic_accuracy": 2,
                "winner_safety": 4,
                "loser_safety": 3,
            },
        })
        assert resp.status_code == 200
        ratings_resp = await client.get("/elo/ratings")
        winner = next(r for r in ratings_resp.json() if r["model_id"] == "model-A")
        assert winner["diagnostic_accuracy_elo"] != 1500
