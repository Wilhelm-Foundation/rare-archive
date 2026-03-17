"""
title: Orphanet Disease Search
description: Search Orphanet for rare disease information, prevalence, and associated genes
author: Wilhelm Foundation
version: 0.1.0
license: Apache-2.0
"""

import json

import httpx


class Tools:
    def __init__(self):
        self.base_url = "https://api.orphadata.com/rd-api/"

    async def orphanet_search(
        self,
        disease_name: str,
        __event_emitter__=None,
    ) -> str:
        """
        Search Orphanet for information about a rare disease including prevalence, inheritance, and associated genes.

        :param disease_name: The name of the rare disease to search for
        :return: JSON string with disease information from Orphanet
        """
        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"description": f"Searching Orphanet for {disease_name}..."}})

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}diseases/search",
                params={"query": disease_name, "lang": "en"},
            )
            results = resp.json()

        diseases = results.get("results", [])
        if not diseases:
            return json.dumps({"found": False, "message": f"No Orphanet entries for '{disease_name}'"})

        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"description": f"Found {len(diseases)} results", "done": True}})

        return json.dumps({
            "found": True,
            "query": disease_name,
            "total_results": len(diseases),
            "diseases": diseases[:5],
        }, indent=2)
