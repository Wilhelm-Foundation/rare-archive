"""
title: ClinVar Variant Lookup
description: Look up variant pathogenicity classifications in NCBI ClinVar
author: Wilhelm Foundation
version: 0.1.0
license: Apache-2.0
"""

import json
from typing import Any

import httpx


class Tools:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    async def clinvar_lookup(
        self,
        variant: str,
        gene: str = "",
        __event_emitter__=None,
    ) -> str:
        """
        Look up a genetic variant in ClinVar to check its clinical significance and pathogenicity classification.

        :param variant: The variant to look up (e.g., 'NM_000546.6:c.215C>G', 'rs28934578', or 'BRCA1 c.5266dupC')
        :param gene: Optional gene symbol to narrow the search
        :return: JSON string with variant classification results
        """
        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"description": f"Searching ClinVar for {variant}..."}})

        query = f"{variant} AND {gene}[gene]" if gene else variant

        async with httpx.AsyncClient() as client:
            # Search
            search_resp = await client.get(
                f"{self.base_url}esearch.fcgi",
                params={"db": "clinvar", "term": query, "retmode": "json", "retmax": 5},
            )
            search_data = search_resp.json()
            ids = search_data.get("esearchresult", {}).get("idlist", [])

            if not ids:
                return json.dumps({"found": False, "message": f"No ClinVar entries found for '{variant}'"})

            # Fetch top result
            fetch_resp = await client.get(
                f"{self.base_url}esummary.fcgi",
                params={"db": "clinvar", "id": ",".join(ids[:3]), "retmode": "json"},
            )
            details = fetch_resp.json()

        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"description": f"Found {len(ids)} ClinVar entries", "done": True}})

        return json.dumps({
            "found": True,
            "query": variant,
            "total_results": int(search_data.get("esearchresult", {}).get("count", 0)),
            "results": details.get("result", {}),
        }, indent=2)
