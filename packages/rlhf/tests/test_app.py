"""Tests for the FastAPI application."""


class TestApp:
    """Tests for app-level behavior."""

    async def test_health_endpoint(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "rare-archive-api"

    async def test_all_routers_mounted(self, client):
        endpoints = [
            "/elo/ratings",
            "/experts/",
            "/evaluations/stats",
            "/preferences/pairs",
        ]
        for endpoint in endpoints:
            resp = await client.get(endpoint)
            assert resp.status_code == 200, f"Router not mounted: {endpoint}"

    async def test_cors_headers(self, client):
        resp = await client.get(
            "/health",
            headers={"origin": "http://example.com"},
        )
        assert resp.status_code == 200
        assert "access-control-allow-origin" in resp.headers
