"""API key authentication for the Archive API.

All mutating endpoints and sensitive reads require a valid X-API-Key header.
The key is validated against the ARCHIVE_API_KEY environment variable.

Fail-closed: if ARCHIVE_API_KEY is not set, protected endpoints return 503.
"""

import os

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str | None = Depends(_api_key_header),
) -> str:
    """FastAPI dependency that validates the X-API-Key header.

    Returns the validated key string (callers assign to _key since unused).
    """
    expected = os.getenv("ARCHIVE_API_KEY", "")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server authentication not configured (ARCHIVE_API_KEY unset)",
        )
    if not api_key or api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key
