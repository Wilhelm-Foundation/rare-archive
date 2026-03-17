"""
title: gnomAD Allele Frequency
description: Look up population allele frequencies in gnomAD
author: Wilhelm Foundation
version: 0.1.0
license: Apache-2.0
"""

import json

import httpx


class Tools:
    def __init__(self):
        self.api_url = "https://gnomad.broadinstitute.org/api/"

    async def gnomad_lookup(
        self,
        variant_id: str,
        __event_emitter__=None,
    ) -> str:
        """
        Look up a variant's population allele frequency in gnomAD for variant interpretation.

        :param variant_id: Variant in chrom-pos-ref-alt format (e.g., '1-55505647-C-T')
        :return: JSON string with population frequency data
        """
        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"description": f"Querying gnomAD for {variant_id}..."}})

        query = """
        query($variantId: String!) {
            variant(variantId: $variantId, dataset: gnomad_r4) {
                variant_id
                rsids
                genome { ac an af }
                exome { ac an af }
            }
        }
        """

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.api_url,
                json={"query": query, "variables": {"variantId": variant_id}},
            )
            data = resp.json()

        variant = data.get("data", {}).get("variant")

        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"done": True}})

        if not variant:
            return json.dumps({"found": False, "variant_id": variant_id})

        return json.dumps({
            "found": True,
            "variant_id": variant.get("variant_id"),
            "rsids": variant.get("rsids", []),
            "genome_af": variant.get("genome", {}).get("af"),
            "exome_af": variant.get("exome", {}).get("af"),
        }, indent=2)
