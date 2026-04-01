"""
title: Differential Diagnosis
description: Generate ranked differential diagnoses using multiple clinical databases
author: Wilhelm Foundation
version: 0.2.0
license: Apache-2.0
"""

import json
import logging

import httpx

logger = logging.getLogger(__name__)


class Tools:
    def __init__(self):
        self.hpo_url = "https://ontology.jax.org/api/hp/"
        self.orphanet_url = "https://api.orphadata.com/"

    async def differential_diagnosis(
        self,
        symptoms: str,
        age: str = "",
        sex: str = "",
        __event_emitter__=None,
    ) -> str:
        """
        Generate a ranked differential diagnosis based on clinical symptoms using HPO term matching.

        :param symptoms: Comma-separated list of symptoms or HPO terms
        :param age: Patient age (optional, e.g., '5 years', 'neonatal')
        :param sex: Patient sex (optional, 'male' or 'female')
        :return: JSON string with ranked differential diagnoses
        """
        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"description": "Analyzing symptoms..."}})

        symptom_list = [s.strip() for s in symptoms.split(",")]

        # Resolve symptoms to HPO terms
        hpo_terms = []
        async with httpx.AsyncClient() as client:
            for symptom in symptom_list:
                if symptom.startswith("HP:"):
                    hpo_terms.append(symptom)
                else:
                    resp = await client.get(f"{self.hpo_url}search", params={"q": symptom, "max": 1})
                    results = resp.json()
                    terms = results.get("terms", results.get("results", []))
                    if terms:
                        hpo_terms.append(terms[0].get("id", symptom))

        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"description": f"Resolved {len(hpo_terms)} HPO terms, computing differentials..."}})

        # Get diseases for each HPO term via Orphanet phenotype API
        disease_scores: dict[str, float] = {}
        failed_terms = 0
        async with httpx.AsyncClient(timeout=30) as client:
            for term in hpo_terms[:10]:
                try:
                    resp = await client.get(f"{self.orphanet_url}rd-phenotypes/hpoids/{term}")
                    if resp.status_code != 200:
                        logger.warning("Orphanet phenotype lookup failed for %s: HTTP %d", term, resp.status_code)
                        failed_terms += 1
                        continue
                    data = resp.json()
                    results = data.get("data", {}).get("results", [])
                    for item in results:
                        disorder = item.get("Disorder", {})
                        name = disorder.get("Preferred term", "Unknown")
                        if name != "Unknown":
                            disease_scores[name] = disease_scores.get(name, 0) + 1
                except Exception as e:
                    logger.warning("Failed to resolve phenotype associations for %s: %s", term, e)
                    failed_terms += 1
                    continue

        # Rank by number of matching HPO terms
        ranked = sorted(disease_scores.items(), key=lambda x: x[1], reverse=True)

        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"done": True}})

        result = {
            "input_symptoms": symptom_list,
            "resolved_hpo_terms": hpo_terms,
            "differentials": [
                {"rank": i + 1, "disease": name, "matching_terms": int(score)}
                for i, (name, score) in enumerate(ranked[:20])
            ],
            "note": "Ranked by number of matching HPO terms via Orphanet. Clinical judgement required.",
        }

        if failed_terms > 0 and len(hpo_terms) > 0 and failed_terms / len(hpo_terms) > 0.5:
            result["warning"] = (
                f"{failed_terms} of {len(hpo_terms)} phenotype terms could not be "
                f"resolved -- results may be incomplete. Check Orphanet API availability."
            )

        return json.dumps(result, indent=2)
