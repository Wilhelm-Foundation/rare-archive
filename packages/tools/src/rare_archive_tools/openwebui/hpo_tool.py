"""
title: HPO Phenotype Lookup
description: Resolve clinical phenotypes to HPO terms and explore phenotype-disease associations
author: Wilhelm Foundation
version: 0.1.0
license: Apache-2.0
"""

import json

import httpx


class Tools:
    def __init__(self):
        self.base_url = "https://ontology.jax.org/api/hp/"

    async def hpo_lookup(
        self,
        phenotype: str,
        __event_emitter__=None,
    ) -> str:
        """
        Search the Human Phenotype Ontology for terms matching a clinical phenotype description.

        :param phenotype: Clinical phenotype description (e.g., 'progressive muscle weakness', 'seizures')
        :return: JSON string with matching HPO terms
        """
        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"description": f"Searching HPO for '{phenotype}'..."}})

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}search",
                params={"q": phenotype, "max": 10},
            )
            results = resp.json()

        terms = results.get("terms", results.get("results", []))

        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"description": f"Found {len(terms)} HPO terms", "done": True}})

        return json.dumps({
            "found": bool(terms),
            "query": phenotype,
            "terms": terms[:5],
        }, indent=2)
