"""ChromaDB integration via REST API (httpx).

Uses ChromaDB's v1 HTTP API directly — no chromadb pip dependency needed.
Stores clinical corrections with embeddings for RAG-style retrieval.
ChromaDB handles embedding via its default model (all-MiniLM-L6-v2).

Target: chromadb/chroma:0.5.23 (v1 API at /api/v1/).
"""

import json
import logging
from typing import Any

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "clinical_corrections"


def _base_url() -> str:
    return settings.chromadb_url.rstrip("/")


def _api(path: str) -> str:
    """Build a v1 API URL."""
    return f"{_base_url()}/api/v1{path}"


async def _ensure_collection() -> str:
    """Get or create the clinical_corrections collection. Returns collection ID."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Try to get existing collection
        resp = await client.get(_api(f"/collections/{COLLECTION_NAME}"))
        if resp.status_code == 200:
            return resp.json()["id"]

        # Create collection
        resp = await client.post(_api("/collections"), json={
            "name": COLLECTION_NAME,
            "metadata": {"description": "Clinical diagnostic corrections for RAG retrieval"},
            "get_or_create": True,
        })
        if resp.status_code in (200, 201):
            return resp.json()["id"]

        raise RuntimeError(f"Failed to create ChromaDB collection: {resp.text}")


async def store_correction(
    case_id: str,
    correction_text: str,
    metadata: dict[str, Any] | None = None,
) -> dict:
    """Upsert a correction into the clinical_corrections collection.

    ChromaDB generates embeddings automatically from the document text.
    """
    collection_id = await _ensure_collection()

    doc_id = f"correction_{case_id}"
    meta = {
        "case_id": case_id,
        "type": "diagnostic_correction",
    }
    if metadata:
        meta.update({k: str(v) for k, v in metadata.items()})

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            _api(f"/collections/{collection_id}/upsert"),
            json={
                "ids": [doc_id],
                "documents": [correction_text],
                "metadatas": [meta],
            },
        )

        if resp.status_code in (200, 201):
            logger.info(f"Stored correction for case {case_id} in ChromaDB")
            return {"status": "stored", "id": doc_id}

        logger.error(f"ChromaDB store failed: {resp.status_code} {resp.text}")
        return {"status": "failed", "error": resp.text}


async def search_corrections(
    query_text: str,
    n_results: int = 5,
) -> list[dict]:
    """Search for similar corrections using ChromaDB's embedding search."""
    collection_id = await _ensure_collection()

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            _api(f"/collections/{collection_id}/query"),
            json={
                "query_texts": [query_text],
                "n_results": n_results,
            },
        )

        if resp.status_code != 200:
            logger.error(f"ChromaDB search failed: {resp.status_code} {resp.text}")
            return []

        data = resp.json()
        results = []
        ids = data.get("ids", [[]])[0]
        documents = data.get("documents", [[]])[0]
        metadatas = data.get("metadatas", [[]])[0]
        distances = data.get("distances", [[]])[0]

        for i, doc_id in enumerate(ids):
            results.append({
                "id": doc_id,
                "document": documents[i] if i < len(documents) else "",
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "distance": distances[i] if i < len(distances) else None,
            })

        return results


async def export_corrections_jsonl() -> str:
    """Dump all corrections from the collection as JSONL string."""
    collection_id = await _ensure_collection()

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            _api(f"/collections/{collection_id}/get"),
            json={},
        )

        if resp.status_code != 200:
            logger.error(f"ChromaDB export failed: {resp.status_code} {resp.text}")
            return ""

        data = resp.json()
        lines = []
        ids = data.get("ids", [])
        documents = data.get("documents", [])
        metadatas = data.get("metadatas", [])

        for i, doc_id in enumerate(ids):
            record = {
                "id": doc_id,
                "document": documents[i] if i < len(documents) else "",
                "metadata": metadatas[i] if i < len(metadatas) else {},
            }
            lines.append(json.dumps(record, ensure_ascii=False))

        return "\n".join(lines)
