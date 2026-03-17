"""Base adapter interface for clinical tool APIs.

All tool adapters inherit from BaseAdapter, which provides:
- Rate limiting (configurable per-tool)
- Redis-backed response caching
- Retry logic with exponential backoff
- Structured error handling
"""

import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    requests_per_second: float = 3.0
    requests_per_day: int = 10000
    burst: int = 10


@dataclass
class CacheConfig:
    """Caching configuration."""
    enabled: bool = True
    backend: str = "redis"  # redis, local, none
    ttl_seconds: int = 3600  # 1 hour default
    redis_url: str = "redis://localhost:6379/1"


@dataclass
class AdapterConfig:
    """Configuration for a tool adapter."""
    base_url: str
    auth_type: str = "none"  # none, api_key, oauth2
    api_key: str = ""
    timeout_seconds: float = 30.0
    max_retries: int = 3
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)


class BaseAdapter(ABC):
    """Base class for all clinical tool API adapters."""

    def __init__(self, config: AdapterConfig):
        self.config = config
        self._client = httpx.Client(
            base_url=config.base_url,
            timeout=config.timeout_seconds,
            headers=self._build_headers(),
        )
        self._last_request_time = 0.0
        self._request_count_today = 0
        self._cache: dict[str, Any] = {}  # Local fallback cache

    def _build_headers(self) -> dict[str, str]:
        headers = {"User-Agent": "RareArchiveToolHarness/0.1.0"}
        if self.config.auth_type == "api_key" and self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def _rate_limit(self):
        """Enforce rate limiting."""
        now = time.monotonic()
        elapsed = now - self._last_request_time
        min_interval = 1.0 / self.config.rate_limit.requests_per_second

        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

        self._last_request_time = time.monotonic()
        self._request_count_today += 1

    def _cache_key(self, endpoint: str, params: dict) -> str:
        """Generate cache key from endpoint and parameters."""
        key_data = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def _get_cached(self, key: str) -> Any | None:
        """Get a cached response."""
        if not self.config.cache.enabled:
            return None

        if self.config.cache.backend == "redis":
            try:
                import redis
                r = redis.from_url(self.config.cache.redis_url)
                data = r.get(f"rare_tool:{key}")
                if data:
                    return json.loads(data)
            except Exception:
                pass  # Fall through to local cache

        return self._cache.get(key)

    def _set_cached(self, key: str, value: Any):
        """Cache a response."""
        if not self.config.cache.enabled:
            return

        if self.config.cache.backend == "redis":
            try:
                import redis
                r = redis.from_url(self.config.cache.redis_url)
                r.setex(
                    f"rare_tool:{key}",
                    self.config.cache.ttl_seconds,
                    json.dumps(value),
                )
                return
            except Exception:
                pass

        self._cache[key] = value

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        json_body: dict | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request with rate limiting, caching, and retries."""
        # Check cache
        cache_key = self._cache_key(endpoint, params or json_body or {})
        cached = self._get_cached(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit: {endpoint}")
            return cached

        # Rate limit
        self._rate_limit()

        # Request with retries
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                response = self._client.request(
                    method,
                    endpoint,
                    params=params,
                    json=json_body,
                )
                response.raise_for_status()
                result = response.json()

                # Cache successful response
                self._set_cached(cache_key, result)
                return result

            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning(f"Rate limited, waiting {wait}s")
                    time.sleep(wait)
                elif e.response.status_code >= 500:
                    wait = 2 ** attempt
                    logger.warning(f"Server error {e.response.status_code}, retrying in {wait}s")
                    time.sleep(wait)
                else:
                    raise
            except httpx.RequestError as e:
                last_error = e
                wait = 2 ** attempt
                logger.warning(f"Request error: {e}, retrying in {wait}s")
                time.sleep(wait)

        raise RuntimeError(f"Failed after {self.config.max_retries} retries: {last_error}")

    @abstractmethod
    def tool_name(self) -> str:
        """Return the tool's name."""
        ...

    @abstractmethod
    def tool_description(self) -> str:
        """Return the tool's description."""
        ...

    def close(self):
        """Close the HTTP client."""
        self._client.close()
