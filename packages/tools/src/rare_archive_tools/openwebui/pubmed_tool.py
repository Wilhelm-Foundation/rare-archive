"""
title: PubMed Literature Search
description: Search PubMed for relevant medical literature on rare diseases
author: Wilhelm Foundation
version: 0.1.0
license: Apache-2.0
"""

import json

import httpx


class Tools:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    async def pubmed_search(
        self,
        query: str,
        max_results: int = 5,
        __event_emitter__=None,
    ) -> str:
        """
        Search PubMed for medical literature relevant to a rare disease query.

        :param query: Search query (disease name, gene, phenotype, etc.)
        :param max_results: Maximum number of results to return (default 5)
        :return: JSON string with article PMIDs and summaries
        """
        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"description": f"Searching PubMed for '{query}'..."}})

        async with httpx.AsyncClient() as client:
            search_resp = await client.get(
                f"{self.base_url}esearch.fcgi",
                params={"db": "pubmed", "term": query, "retmode": "json", "retmax": max_results, "sort": "relevance"},
            )
            search_data = search_resp.json()
            ids = search_data.get("esearchresult", {}).get("idlist", [])

            if not ids:
                return json.dumps({"found": False, "query": query})

            summary_resp = await client.get(
                f"{self.base_url}esummary.fcgi",
                params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
            )
            summaries = summary_resp.json()

        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"description": f"Found {len(ids)} articles", "done": True}})

        return json.dumps({
            "found": True,
            "query": query,
            "total": int(search_data.get("esearchresult", {}).get("count", 0)),
            "articles": summaries.get("result", {}),
        }, indent=2)
