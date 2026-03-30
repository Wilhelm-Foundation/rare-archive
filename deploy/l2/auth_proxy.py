#!/usr/bin/env python3
"""Rare Archive Auth Proxy — validates JupyterHub sessions for OpenWebUI.

Sits between NGINX (auth_request) and JupyterHub. When NGINX receives a
request for OpenWebUI paths, it sends a subrequest to this service. We
validate the jupyterhub-session-id cookie by querying Hub's PostgreSQL
database (api_tokens.session_id → users.name), then return the user's
email in a response header that NGINX captures via auth_request_set.

Why PostgreSQL instead of Hub API: JupyterHub 5.0 removed the
/api/authorizations/cookie/ endpoint, and the jupyterhub-hub-login cookie
has path=/hub/ (browser won't send it for non-/hub/ paths). The
jupyterhub-session-id cookie (path=/) IS always sent and maps directly
to api_tokens.session_id in the database.

Environment:
    DATABASE_URL: PostgreSQL connection string for JupyterHub database
    EMAIL_DOMAIN: Domain suffix for user emails (default: lattice.bio)
    LISTEN_PORT: Port to listen on (default: 8090)
"""

import logging
import os

from fastapi import FastAPI, Request
from fastapi.responses import Response
import psycopg2
from psycopg2.pool import SimpleConnectionPool

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("auth-proxy")

app = FastAPI(docs_url=None, redoc_url=None)

DATABASE_URL = os.getenv("DATABASE_URL", "")
EMAIL_DOMAIN = os.getenv("EMAIL_DOMAIN", "lattice.bio")

# Admin users who should keep their existing OpenWebUI email
ADMIN_EMAILS = {
    "stanley": "science.stanley@stanley.science",
    "herb": "herb@lattice.bio",
}

# Connection pool (initialized on first request)
_pool = None

VALIDATE_SQL = """
SELECT u.name
FROM api_tokens t
JOIN users u ON t.user_id = u.id
WHERE t.session_id = %s
ORDER BY t.last_activity DESC
LIMIT 1
"""


def _get_pool():
    global _pool
    if _pool is None:
        _pool = SimpleConnectionPool(1, 5, DATABASE_URL)
    return _pool


def _user_to_email(username: str) -> str:
    """Map JupyterHub username to email for OpenWebUI."""
    return ADMIN_EMAILS.get(username, f"{username}@{EMAIL_DOMAIN}")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/validate")
async def validate(request: Request):
    """Validate JupyterHub session cookie. Called by NGINX auth_request.

    Reads jupyterhub-session-id cookie (path=/, always sent by browser)
    and looks up the associated user in Hub's PostgreSQL database.

    Returns:
        200 + X-Auth-User-Email header if authenticated
        401 if not authenticated
    """
    session_id = request.cookies.get("jupyterhub-session-id")
    if not session_id:
        return Response(status_code=401, content="No Hub session")

    try:
        pool = _get_pool()
        conn = pool.getconn()
        try:
            cur = conn.cursor()
            cur.execute(VALIDATE_SQL, (session_id,))
            row = cur.fetchone()
            cur.close()
        finally:
            pool.putconn(conn)

        if row:
            username = row[0]
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
            log.debug("No user for session: %s", session_id[:8])
            return Response(status_code=401, content="Invalid session")
    except Exception as e:
        log.error("DB error: %s", e)
        return Response(status_code=401, content="Auth service error")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("LISTEN_PORT", "8090"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
