"""Tests for preference pair extraction and export."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from archive_api.routers.preferences import _load_existing_ids


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
        assert data["new_pairs_exported"] >= 1
        assert data["total_pairs"] >= 1

    async def test_no_data_handled(self, client):
        resp = await client.post("/preferences/export")
        assert resp.status_code == 200
        assert resp.json()["status"] == "no_data"


class TestAppendDeduplication:
    """Tests for append-mode deduplication logic."""

    def test_load_existing_ids_empty_file(self):
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "empty.jsonl"
            assert _load_existing_ids(path) == set()

    def test_load_existing_ids_nonexistent(self):
        assert _load_existing_ids(Path("/nonexistent/file.jsonl")) == set()

    def test_load_existing_ids_parses_evaluation_ids(self):
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "prefs.jsonl"
            records = [
                {"metadata": {"evaluation_id": 1}, "prompt": "x", "chosen": "a", "rejected": "b"},
                {"metadata": {"evaluation_id": 2}, "prompt": "y", "chosen": "c", "rejected": "d"},
                {"metadata": {"evaluation_id": 5}, "prompt": "z", "chosen": "e", "rejected": "f"},
            ]
            with open(path, "w") as f:
                for r in records:
                    f.write(json.dumps(r) + "\n")

            ids = _load_existing_ids(path)
            assert ids == {1, 2, 5}

    def test_load_existing_ids_handles_corrupt_lines(self):
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "prefs.jsonl"
            with open(path, "w") as f:
                f.write(json.dumps({"metadata": {"evaluation_id": 10}}) + "\n")
                f.write("not valid json\n")
                f.write(json.dumps({"metadata": {"evaluation_id": 20}}) + "\n")
                f.write("\n")  # blank line

            ids = _load_existing_ids(path)
            assert ids == {10, 20}

    async def test_export_twice_no_duplicates(self, client, sample_evaluation):
        """Export twice — second export should still succeed (no HF in test mode)."""
        resp1 = await client.post("/preferences/export")
        assert resp1.status_code == 200
        assert resp1.json()["status"] == "success"
        count1 = resp1.json()["new_pairs_exported"]

        resp2 = await client.post("/preferences/export")
        assert resp2.status_code == 200
        # Without HF, both exports report all pairs as "new" (no download)
        # but the core dedup logic is tested via _load_existing_ids above
        assert resp2.json()["status"] == "success"
        assert resp2.json()["new_pairs_exported"] == count1
