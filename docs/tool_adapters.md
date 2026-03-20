# Tool Adapter Reference — Rare AI Archive

Per-tool documentation for all 7 clinical diagnostic tool integrations. Each tool has a Python adapter (`packages/tools/src/rare_archive_tools/adapters/`) and an OpenWebUI wrapper (`packages/tools/src/rare_archive_tools/openwebui/`).

For architecture details and the "add a new tool" checklist, see [tool_integration_spec.md](tool_integration_spec.md).

---

## ClinVar

**Source**: NCBI E-Utilities | **Adapter**: `adapters/clinvar.py` | **OpenWebUI**: `clinvar_tool.py`

**Purpose**: Variant pathogenicity classification from the NCBI ClinVar database.

**Input**: Variant description (HGVS notation, rsID, or free text) + optional gene symbol filter.

**Output**: Pathogenicity classification, review status, associated conditions, variant ID, total matching results.

**API Endpoint**: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`

**Methods**:
- `search_variant(variant, gene=None)` — E-Search ClinVar for variant IDs
- `fetch_variant(variant_id)` — E-Fetch detailed VCV record
- `lookup(variant, gene=None)` — Combined search + fetch (primary entry point)

**Authentication**: Optional NCBI API key (increases rate limit from 3 to 10 req/s). Optional email parameter.

**Rate limit**: 3 req/s without API key, 10 req/s with API key.

**Known limitations**:
- E-Fetch returns XML-structured JSON that requires careful parsing
- Some rare variants have no ClinVar entry despite being pathogenic
- VCV records can be very large for well-studied variants (e.g., BRCA1)

**Example**:
```python
from rare_archive_tools.adapters.clinvar import ClinVarAdapter

clinvar = ClinVarAdapter(api_key="your_key")
result = clinvar.lookup("BRCA1 c.5266dupC")
# result["found"] = True, result["variant_id"] = "...", result["total_results"] = N
```

---

## Orphanet

**Source**: Orphadata REST API | **Adapter**: `adapters/orphanet.py` | **OpenWebUI**: `orphanet_tool.py`

**Purpose**: Rare disease information — disease definitions, associated genes, HPO phenotypes, and epidemiology.

**Input**: Disease name (free text) or ORPHA code.

**Output**: Disease name, ORPHA code, disorder group, cross-referencing data, associated genes, phenotypes.

**API Endpoint**: `https://api.orphadata.com/`

**Methods**:
- `search_disease(query)` — Search by disease name via `rd-cross-referencing/orphacodes/names/{name}`
- `get_disease(orpha_code)` — Cross-referencing data by ORPHA code
- `get_disease_genes(orpha_code)` — Associated genes via `rd-associated-genes/`
- `get_disease_phenotypes(orpha_code)` — HPO phenotypes via `rd-phenotypes/`
- `lookup(disease_name)` — Name search with structured result (primary entry point)

**Authentication**: None required.

**Rate limit**: ~1 req/s (no official documentation; empirically determined).

**Known limitations**:
- API was restructured in 2025 — older endpoint patterns no longer work
- Not all diseases have phenotype annotations (~53% hit rate for HPO terms)
- Name matching is exact-ish — partial names may miss results
- `get_disease_genes` and `get_disease_phenotypes` require a separate call per disease

**Example**:
```python
from rare_archive_tools.adapters.orphanet import OrphanetAdapter

orphanet = OrphanetAdapter()
result = orphanet.lookup("Marfan syndrome")
# result["found"] = True, result["orpha_code"] = "558", result["disorder_group"] = "Disorder"
genes = orphanet.get_disease_genes("558")
```

---

## HPO (Human Phenotype Ontology)

**Source**: HPO JAX API | **Adapter**: `adapters/hpo.py` | **OpenWebUI**: `hpo_tool.py`

**Purpose**: Resolve clinical phenotype descriptions to standardized HPO terms and explore phenotype relationships.

**Input**: Clinical phenotype description (free text) or HPO ID (e.g., `HP:0001250`).

**Output**: Matching HPO terms with IDs, associated diseases, associated genes.

**API Endpoint**: `https://ontology.jax.org/api/hp/`

**Methods**:
- `search_term(query, max_results=10)` — Full-text search for HPO terms
- `get_term(hpo_id)` — Details for a specific HPO term
- `get_term_diseases(hpo_id)` — Diseases associated with a term
- `get_term_genes(hpo_id)` — Genes associated with a term
- `lookup(phenotype_description)` — Search + return top 5 terms (primary entry point)

**Authentication**: None required.

**Rate limit**: ~2 req/s (empirically determined).

**Known limitations**:
- Some API endpoints were removed/changed in early 2026
- Free-text search quality varies — clinical shorthand may not match well
- Disease associations may include common diseases if HPO term is broad

**Example**:
```python
from rare_archive_tools.adapters.hpo import HPOAdapter

hpo = HPOAdapter()
result = hpo.lookup("seizures")
# result["found"] = True, result["total_results"] = N, result["terms"] = [...]
diseases = hpo.get_term_diseases("HP:0001250")
```

---

## PanelApp

**Source**: Genomics England PanelApp API | **Adapter**: `adapters/panelapp.py` | **OpenWebUI**: `panelapp_tool.py`

**Purpose**: Query curated gene panels for diagnostic testing — which genes to test for a given disease.

**Input**: Disease name, gene symbol, or panel ID.

**Output**: Gene panels with names, disease groups, gene counts, confidence levels, panel versions.

**API Endpoint**: `https://panelapp.genomicsengland.co.uk/api/v1/`

**Methods**:
- `search_panels(query)` — Search panels by name or disease
- `get_panel(panel_id, version=None)` — Get specific panel with full gene list
- `search_genes(gene_symbol)` — Search for a gene across all panels
- `lookup(query)` — Panel search with structured results (primary entry point)

**Authentication**: None required.

**Rate limit**: ~2 req/s (empirically determined).

**Known limitations**:
- UK-centric gene panels — may not reflect all international clinical practices
- Panel versions change frequently; pin version for reproducibility
- `search_genes` returns all panels containing a gene — can be noisy for common genes

**Example**:
```python
from rare_archive_tools.adapters.panelapp import PanelAppAdapter

panelapp = PanelAppAdapter()
result = panelapp.lookup("epilepsy")
# result["found"] = True, result["total_results"] = N, result["panels"] = [...]
panel = panelapp.get_panel("123")
```

---

## gnomAD

**Source**: gnomAD GraphQL API | **Adapter**: `adapters/gnomad.py` | **OpenWebUI**: `gnomad_tool.py`

**Purpose**: Population allele frequency lookup for variant interpretation (distinguishing pathogenic from benign).

**Input**: Variant ID in `chrom-pos-ref-alt` format (e.g., `1-55505647-C-T`).

**Output**: Genome and exome allele frequencies, allele counts, population breakdowns, rsIDs.

**API Endpoint**: `https://gnomad.broadinstitute.org/api/`

**Methods**:
- `query_variant(variant_id, dataset="gnomad_r4")` — Full GraphQL query with population breakdowns
- `lookup(variant_id)` — Simplified frequency lookup (primary entry point)

**Authentication**: None required.

**Rate limit**: ~5 req/s (empirically determined).

**Known limitations**:
- GraphQL schema changes are possible between gnomAD versions
- Variant ID format is strict (`chrom-pos-ref-alt`) — no HGVS input
- Some populations have very low sample counts — frequencies may be unreliable
- Response payload is large (all populations returned)

**Example**:
```python
from rare_archive_tools.adapters.gnomad import GnomADAdapter

gnomad = GnomADAdapter()
result = gnomad.lookup("1-55505647-C-T")
# result["found"] = True, result["genome_af"] = 0.0001, result["exome_af"] = 0.00012
```

---

## PubMed

**Source**: NCBI E-Utilities | **Adapter**: `adapters/pubmed.py` | **OpenWebUI**: `pubmed_tool.py`

**Purpose**: Medical literature search for rare disease case reports, reviews, and research papers.

**Input**: Search query (free text, MeSH terms, or structured PubMed query) + optional result limit.

**Output**: PubMed IDs, total result count, article abstracts.

**API Endpoint**: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`

**Methods**:
- `search(query, max_results=5)` — E-Search PubMed sorted by relevance
- `fetch_abstracts(pmids)` — E-Fetch article details for a list of PMIDs
- `lookup(query, max_results=5)` — Combined search returning PMIDs (primary entry point)

**Authentication**: Optional NCBI API key (increases rate limit from 3 to 10 req/s). Optional email parameter.

**Rate limit**: 3 req/s without API key, 10 req/s with API key (shared with ClinVar).

**Known limitations**:
- Rate limit is shared across all NCBI E-Utility calls (ClinVar + PubMed)
- Abstract fetch can be slow for many PMIDs — keep `max_results` reasonable
- Some articles have no abstract available
- Relevance sorting may not surface rare disease papers for broad queries

**Example**:
```python
from rare_archive_tools.adapters.pubmed import PubMedAdapter

pubmed = PubMedAdapter(api_key="your_key")
result = pubmed.lookup("Marfan syndrome gene therapy", max_results=3)
# result["found"] = True, result["total_results"] = N, result["pmids"] = [...]
```

---

## Differential Diagnosis (Composite)

**Source**: HPO JAX + Orphadata (composite) | **OpenWebUI**: `differential_dx_tool.py`

**Purpose**: Generate ranked differential diagnoses from clinical symptoms using HPO term resolution and Orphanet disease-phenotype matching.

**Input**: Comma-separated symptoms (free text or HPO terms) + optional age and sex.

**Output**: Ranked list of candidate diagnoses with matching HPO term counts.

**Architecture**: Unlike the other 6 tools, Differential Dx has no standalone adapter — it is implemented directly as an OpenWebUI tool that orchestrates HPO and Orphanet APIs internally.

**API Endpoints used**:
- `https://ontology.jax.org/api/hp/search` — HPO term resolution
- `https://api.orphadata.com/rd-phenotypes/hpoids/{term}` — Disease-to-phenotype reverse lookup

**Authentication**: None required.

**Rate limit**: Inherits from HPO (~2 req/s) and Orphanet (~1 req/s). A 10-symptom query makes up to 20 API calls.

**Algorithm**:
1. Resolve each symptom to an HPO term (exact match for `HP:` prefixed, search for free text)
2. For each HPO term, query Orphanet for diseases with that phenotype
3. Score diseases by number of matching HPO terms
4. Rank and return top 20 candidates

**Known limitations**:
- Ranking is simplistic (term count only) — does not weight by phenotype frequency
- Limited to 10 HPO terms per query (to manage API call volume)
- Orphanet phenotype coverage varies — ~53% of diseases have phenotype annotations
- Age and sex parameters are accepted but not currently used in scoring
- Async-only implementation (OpenWebUI tool pattern)

**Example** (via OpenWebUI chat):
```
User: What rare diseases match these symptoms: seizures, developmental delay, hepatomegaly?
→ Tool calls differential_diagnosis("seizures, developmental delay, hepatomegaly")
→ Returns ranked list of ~20 candidate diagnoses
```
