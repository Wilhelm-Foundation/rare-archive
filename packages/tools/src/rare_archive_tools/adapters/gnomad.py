"""gnomAD adapter — Population allele frequency lookup."""

from typing import Any

from .base import AdapterConfig, BaseAdapter


class GnomADAdapter(BaseAdapter):
    """Adapter for gnomAD API (GraphQL)."""

    def __init__(self):
        config = AdapterConfig(
            base_url="https://gnomad.broadinstitute.org/api/",
        )
        super().__init__(config)

    def tool_name(self) -> str:
        return "gnomad_allele_frequency"

    def tool_description(self) -> str:
        return "Look up population allele frequencies in gnomAD for variant interpretation"

    def query_variant(self, variant_id: str, dataset: str = "gnomad_r4") -> dict[str, Any]:
        """Query gnomAD for a variant's population frequencies.

        Args:
            variant_id: Variant in format "chrom-pos-ref-alt" (e.g., "1-55505647-C-T")
            dataset: gnomAD dataset version
        """
        query = """
        query GnomadVariant($variantId: String!, $datasetId: DatasetId!) {
            variant(variantId: $variantId, dataset: $datasetId) {
                variant_id
                rsids
                genome {
                    ac
                    an
                    af
                    populations {
                        id
                        ac
                        an
                    }
                }
                exome {
                    ac
                    an
                    af
                    populations {
                        id
                        ac
                        an
                    }
                }
            }
        }
        """

        result = self._request(
            "POST", "",
            json_body={
                "query": query,
                "variables": {"variantId": variant_id, "datasetId": dataset},
            },
        )
        return result

    def lookup(self, variant_id: str) -> dict[str, Any]:
        """Simplified variant frequency lookup."""
        result = self.query_variant(variant_id)
        variant = result.get("data", {}).get("variant")

        if not variant:
            return {"found": False, "query": variant_id}

        return {
            "found": True,
            "variant_id": variant.get("variant_id"),
            "rsids": variant.get("rsids", []),
            "genome_af": variant.get("genome", {}).get("af"),
            "exome_af": variant.get("exome", {}).get("af"),
        }
