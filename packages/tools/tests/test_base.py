"""Tests for the base adapter."""

import httpx
import pytest
import respx

from rare_archive_tools.adapters.base import AdapterConfig, BaseAdapter, CacheConfig


class _DummyAdapter(BaseAdapter):
    """Minimal adapter for testing the base class."""

    def tool_name(self):
        return "dummy"

    def tool_description(self):
        return "A dummy adapter for testing"


def _make_adapter(base_url="https://test.example.com/", cache_enabled=True, **kwargs):
    return _DummyAdapter(AdapterConfig(
        base_url=base_url,
        cache=CacheConfig(enabled=cache_enabled, backend="local"),
        **kwargs,
    ))


class TestCacheKey:
    def test_deterministic(self):
        adapter = _make_adapter()
        k1 = adapter._cache_key("endpoint", {"a": 1})
        k2 = adapter._cache_key("endpoint", {"a": 1})
        assert k1 == k2

    def test_different_params_different_key(self):
        adapter = _make_adapter()
        k1 = adapter._cache_key("endpoint", {"a": 1})
        k2 = adapter._cache_key("endpoint", {"a": 2})
        assert k1 != k2


class TestLocalCache:
    def test_set_get_roundtrip(self):
        adapter = _make_adapter()
        adapter._set_cached("key1", {"data": "value"})
        assert adapter._get_cached("key1") == {"data": "value"}

    def test_miss_returns_none(self):
        adapter = _make_adapter()
        assert adapter._get_cached("nonexistent") is None

    def test_cache_disabled_returns_none(self):
        adapter = _make_adapter(cache_enabled=False)
        adapter._set_cached("key1", {"data": "value"})
        assert adapter._get_cached("key1") is None


class TestRequest:
    @respx.mock
    def test_get_success(self):
        adapter = _make_adapter(cache_enabled=False)
        respx.get("https://test.example.com/endpoint").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        result = adapter._request("GET", "endpoint")
        assert result == {"ok": True}

    @respx.mock
    def test_post_success(self):
        adapter = _make_adapter(cache_enabled=False)
        respx.post("https://test.example.com/endpoint").mock(
            return_value=httpx.Response(200, json={"created": True})
        )
        result = adapter._request("POST", "endpoint", json_body={"key": "val"})
        assert result == {"created": True}

    @respx.mock
    def test_caches_response(self):
        adapter = _make_adapter(cache_enabled=True)
        route = respx.get("https://test.example.com/endpoint").mock(
            return_value=httpx.Response(200, json={"data": 1})
        )
        r1 = adapter._request("GET", "endpoint")
        r2 = adapter._request("GET", "endpoint")
        assert r1 == r2 == {"data": 1}
        assert route.call_count == 1

    @respx.mock
    def test_retry_on_429_then_success(self):
        adapter = _make_adapter(cache_enabled=False)
        route = respx.get("https://test.example.com/endpoint").mock(
            side_effect=[
                httpx.Response(429),
                httpx.Response(200, json={"ok": True}),
            ]
        )
        result = adapter._request("GET", "endpoint")
        assert result == {"ok": True}
        assert route.call_count == 2

    @respx.mock
    def test_raises_after_max_retries(self):
        adapter = _make_adapter(cache_enabled=False, max_retries=3)
        respx.get("https://test.example.com/endpoint").mock(
            side_effect=[
                httpx.Response(429),
                httpx.Response(429),
                httpx.Response(429),
            ]
        )
        with pytest.raises(RuntimeError, match="Failed after 3 retries"):
            adapter._request("GET", "endpoint")


class TestBuildHeaders:
    def test_api_key_adds_bearer(self):
        adapter = _DummyAdapter(AdapterConfig(
            base_url="https://test.example.com/",
            auth_type="api_key",
            api_key="test-key-123",
        ))
        headers = adapter._build_headers()
        assert headers["Authorization"] == "Bearer test-key-123"

    def test_no_auth_no_authorization(self):
        adapter = _DummyAdapter(AdapterConfig(
            base_url="https://test.example.com/",
            auth_type="none",
        ))
        headers = adapter._build_headers()
        assert "Authorization" not in headers


class TestClose:
    @respx.mock
    def test_close_closes_client(self):
        adapter = _make_adapter()
        adapter.close()
        assert adapter._client.is_closed
