#!/usr/bin/env python3
"""Rare Archive Auth Proxy — validates JupyterHub sessions for OpenWebUI.

Sits between NGINX (auth_request) and JupyterHub API. When NGINX receives a
request for /archive/, it sends a subrequest to this service. We validate the
JupyterHub session cookie against the Hub API and return the authenticated
user's email in a response header that NGINX captures via auth_request_set.

Environment:
    JUPYTERHUB_API_URL: Hub API base (default: http://jupyterhub:8081/hub/api)
    JUPYTERHUB_API_TOKEN: Service-level API token for Hub validation
    EMAIL_DOMAIN: Domain suffix for user emails (default: lattice.bio)
    LISTEN_PORT: Port to listen on (default: 8090)
"""

import logging
import os

from fastapi import FastAPI, Request
from fastapi.responses import Response
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("auth-proxy")

app = FastAPI(docs_url=None, redoc_url=None)

HUB_API_URL = os.getenv("JUPYTERHUB_API_URL", "http://jupyterhub:8081/hub/api")
HUB_API_TOKEN = os.getenv("JUPYTERHUB_API_TOKEN", "")
EMAIL_DOMAIN = os.getenv("EMAIL_DOMAIN", "lattice.bio")

# Admin users who should keep their existing OpenWebUI email
ADMIN_EMAILS = {
    "stanley": "science.stanley@stanley.science",
    "herb": "herb@lattice.bio",
}


def _user_to_email(username: str) -> str:
    """Map JupyterHub username to email for OpenWebUI."""
    return ADMIN_EMAILS.get(username, f"{username}@{EMAIL_DOMAIN}")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/validate")
async def validate(request: Request):
    """Validate JupyterHub session cookie. Called by NGINX auth_request.

    Returns:
        200 + X-Auth-User-Email header if authenticated
        401 if not authenticated
    """
    # Extract JupyterHub cookies from the original request
    # NGINX forwards original cookies via proxy_set_header Cookie
    cookies = request.cookies
    hub_cookie = None
    for name, value in cookies.items():
        if name.startswith("jupyterhub-session-id"):
            hub_cookie = (name, value)
            break

    if not hub_cookie:
        log.debug("No JupyterHub session cookie found")
        return Response(status_code=401, content="No Hub session")

    cookie_name, cookie_value = hub_cookie

    # Validate against JupyterHub API
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{HUB_API_URL}/authorizations/cookie/{cookie_name}/{cookie_value}",
                headers={"Authorization": f"token {HUB_API_TOKEN}"},
            )
            if resp.status_code == 200:
                user_data = resp.json()
                username = user_data.get("name", "")
                email = _user_to_email(username)
                log.info("Authenticated: %s -> %s", username, email)
                return Response(
                    status_code=200,
                    headers={
                        "X-Auth-User-Email": email,
                        "X-Auth-User-Name": username,
                    },
                )
            else:
                log.debug("Hub rejected cookie: %s", resp.status_code)
                return Response(status_code=401, content="Invalid session")
    except Exception as e:
        log.error("Hub API error: %s", e)
        return Response(status_code=401, content="Auth service error")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("LISTEN_PORT", "8090"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
