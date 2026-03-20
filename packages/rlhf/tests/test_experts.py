"""Tests for expert registration and matching endpoints."""


class TestRegister:
    """Tests for POST /experts/register."""

    async def test_creates_expert(self, client):
        resp = await client.post("/experts/register", json={
            "username": "dr_jones",
            "display_name": "Dr. Jones",
            "subspecialty": "metabolic",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "dr_jones"
        assert "id" in data

    async def test_duplicate_username_409(self, client, sample_expert):
        resp = await client.post("/experts/register", json={
            "username": "dr_smith",
            "display_name": "Another Smith",
            "subspecialty": "metabolic",
        })
        assert resp.status_code == 409

    async def test_missing_required_fields_422(self, client):
        resp = await client.post("/experts/register", json={
            "username": "test",
        })
        assert resp.status_code == 422


class TestListExperts:
    """Tests for GET /experts/."""

    async def test_returns_all_active(self, client, sample_expert):
        resp = await client.get("/experts/")
        assert resp.status_code == 200
        experts = resp.json()
        assert len(experts) >= 1
        assert experts[0]["username"] == "dr_smith"

    async def test_empty_list_when_none(self, client):
        resp = await client.get("/experts/")
        assert resp.status_code == 200
        assert resp.json() == []


class TestMatchCategory:
    """Tests for GET /experts/match/{patient_category}."""

    async def test_returns_matching(self, client, sample_expert):
        resp = await client.get("/experts/match/neuromuscular")
        assert resp.status_code == 200
        experts = resp.json()
        assert len(experts) == 1
        assert "neuromuscular" in experts[0]["patient_categories"]

    async def test_no_match_empty(self, client, sample_expert):
        resp = await client.get("/experts/match/cardiology")
        assert resp.status_code == 200
        assert resp.json() == []
