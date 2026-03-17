"""
title: PanelApp Gene Panel Query
description: Query Genomics England PanelApp for curated gene panels
author: Wilhelm Foundation
version: 0.1.0
license: Apache-2.0
"""

import json

import httpx


class Tools:
    def __init__(self):
        self.base_url = "https://panelapp.genomicsengland.co.uk/api/v1/"

    async def panelapp_search(
        self,
        query: str,
        __event_emitter__=None,
    ) -> str:
        """
        Search PanelApp for curated gene panels related to a disease or gene.

        :param query: Disease name or gene symbol to search for
        :return: JSON string with matching gene panels
        """
        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"description": f"Searching PanelApp for '{query}'..."}})

        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}panels/", params={"search": query})
            results = resp.json()

        panels = results.get("results", [])

        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"description": f"Found {len(panels)} panels", "done": True}})

        return json.dumps({
            "found": bool(panels),
            "query": query,
            "total": results.get("count", 0),
            "panels": [
                {"id": p.get("id"), "name": p.get("name"), "genes": p.get("stats", {}).get("number_of_genes", 0)}
                for p in panels[:10]
            ],
        }, indent=2)
