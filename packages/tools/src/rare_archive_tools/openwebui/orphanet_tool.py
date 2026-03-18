"""
title: Orphanet Disease Search
description: Search Orphanet for rare disease information, prevalence, and associated genes
author: Wilhelm Foundation
version: 0.2.0
license: Apache-2.0
"""

import json

import httpx


class Tools:
    def __init__(self):
        self.base_url = "https://api.orphadata.com/"

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
                f"{self.base_url}rd-cross-referencing/orphacodes/names/{disease_name}",
            )
            result = resp.json()

        data = result.get("data", {})
        if not data or data.get("__count", 0) == 0:
            return json.dumps({"found": False, "message": f"No Orphanet entries for '{disease_name}'"})

        results = data.get("results", data)
        name = results.get("Preferred term", disease_name)
        orpha_code = results.get("ORPHAcode", "")

        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"description": f"Found: {name} (ORPHA:{orpha_code})", "done": True}})

        return json.dumps({
            "found": True,
            "query": disease_name,
            "name": name,
            "orpha_code": orpha_code,
            "disorder_group": results.get("DisorderGroup", ""),
            "external_references": results.get("ExternalReference", []),
        }, indent=2)
