"""ChromaDB integration via Python client (HttpClient mode).

Uses chromadb-client to connect to the ChromaDB server container.
The client handles embedding via its default model (all-MiniLM-L6-v2),
which enables text-based queries without pre-computing embeddings.

Target: chromadb/chroma:0.5.23 server.
"""

import json
import logging
from typing import Any

import chromadb

from ..config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "clinical_corrections"

_client = None


def _get_client() -> chromadb.HttpClient:
    """Get or create the ChromaDB HTTP client (singleton)."""
    global _client
    if _client is None:
        url = settings.chromadb_url.rstrip("/")
        # Parse host and port from URL
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = parsed.hostname or "rare-archive-chromadb"
        port = parsed.port or 8000
        _client = chromadb.HttpClient(host=host, port=port)
    return _client


def _get_collection():
    """Get or create the clinical_corrections collection."""
    client = _get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Clinical diagnostic corrections for RAG retrieval"},
    )


async def store_correction(
    case_id: str,
    correction_text: str,
    metadata: dict[str, Any] | None = None,
) -> dict:
    """Upsert a correction into the clinical_corrections collection.

    The ChromaDB client generates embeddings automatically from document text.
    """
    collection = _get_collection()

    doc_id = f"correction_{case_id}"
    meta = {
        "case_id": case_id,
        "type": "diagnostic_correction",
    }
    if metadata:
        meta.update({k: str(v) for k, v in metadata.items()})

    collection.upsert(
        ids=[doc_id],
        documents=[correction_text],
        metadatas=[meta],
    )

    logger.info(f"Stored correction for case {case_id} in ChromaDB")
    return {"status": "stored", "id": doc_id}


async def search_corrections(
    query_text: str,
    n_results: int = 5,
) -> list[dict]:
    """Search for similar corrections using ChromaDB's embedding search."""
    collection = _get_collection()

    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query_text],
        n_results=min(n_results, collection.count()),
    )

    output = []
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for i, doc_id in enumerate(ids):
        output.append({
            "id": doc_id,
            "document": documents[i] if i < len(documents) else "",
            "metadata": metadatas[i] if i < len(metadatas) else {},
            "distance": distances[i] if i < len(distances) else None,
        })

    return output


async def export_corrections_jsonl() -> str:
    """Dump all corrections from the collection as JSONL string."""
    collection = _get_collection()

    if collection.count() == 0:
        return ""

    results = collection.get()

    lines = []
    ids = results.get("ids", [])
    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])

    for i, doc_id in enumerate(ids):
        record = {
            "id": doc_id,
            "document": documents[i] if i < len(documents) else "",
            "metadata": metadatas[i] if i < len(metadatas) else {},
        }
        lines.append(json.dumps(record, ensure_ascii=False))

    return "\n".join(lines)
