# Rare AI Archive — Demo Scenarios

Clinical demonstration vignettes for the Rare Disease Specialist system.
Each scenario follows: **Patient Presentation → Tool Invocations → Expected Output → Model Interpretation**.

Base model: Qwen 3.5 35B-A3B (GGUF Q8_0) on L2 GPU 3
Tools: 7 clinical adapters (ClinVar, Orphanet, HPO, PanelApp, gnomAD, PubMed, DiffDx)
Interface: OpenWebUI (L2 port 3100)

---

## Scenario 1: Gaucher Disease — IEM

**Category**: Inborn Errors of Metabolism
**Complexity**: Moderate — classic presentation with confirmatory genetics

### Patient Presentation

> A 28-year-old Ashkenazi Jewish male presents with progressive fatigue, easy bruising, and left upper quadrant fullness. Physical exam reveals hepatosplenomegaly. Labs show thrombocytopenia (platelets 68K), mild anemia, and elevated chitotriosidase. Bone marrow biopsy shows "crinkled paper" macrophages. Genetic testing reveals a homozygous c.1226A>G (N370S) variant in the GBA1 gene.

### Expected Tool Invocations

1. **Orphanet** → `search_disease("Gaucher disease")` → ORPHA:355, Type 1 (non-neuropathic), prevalence 1/57,000 in general population, higher in Ashkenazi Jewish
2. **ClinVar** → `search_variant("c.1226A>G", gene="GBA1")` → Pathogenic, Gaucher disease type 1, N370S most common variant
3. **gnomAD** → `query_variant("1-155235218-T-C")` → AF ~0.03 in Ashkenazi Jewish population (carrier frequency ~1/15)
4. **PubMed** → `search("Gaucher disease GBA1 enzyme replacement therapy")` → ERT (imiglucerase/velaglucerase), substrate reduction (eliglustat)
5. **HPO** → `search_term("hepatosplenomegaly")` → HP:0001433, associated with >200 rare diseases

### Model Interpretation Points

- Confirm Gaucher disease Type 1 (non-neuropathic) based on genotype (N370S/N370S)
- Note: N370S homozygosity is protective against neurological involvement
- Treatment: ERT or SRT, with monitoring of chitotriosidase as biomarker
- Genetic counseling: autosomal recessive, carrier screening relevant for Ashkenazi Jewish community
- Flag GBA1 heterozygosity as risk factor for Parkinson disease (PubMed evidence)

---

## Scenario 2: Phenylketonuria (PKU) — IEM

**Category**: Inborn Errors of Metabolism
**Complexity**: Low — newborn screening positive

### Patient Presentation

> A 5-day-old neonate has a positive newborn screening result showing elevated phenylalanine (Phe) at 22 mg/dL (normal <2 mg/dL). Confirmatory plasma amino acids show Phe of 25 mg/dL with low tyrosine. The infant is otherwise well-appearing. Parents are non-consanguineous of Northern European descent. Genetic testing identifies compound heterozygous variants in PAH: c.1222C>T (R408W) and c.842C>T (P281L).

### Expected Tool Invocations

1. **Orphanet** → `search_disease("Phenylketonuria")` → ORPHA:716, autosomal recessive, incidence 1/10,000
2. **ClinVar** → `search_variant("c.1222C>T", gene="PAH")` → Pathogenic, classic PKU, R408W is the most common European variant
3. **ClinVar** → `search_variant("c.842C>T", gene="PAH")` → Pathogenic, associated with moderate-to-classic PKU
4. **PanelApp** → `search_panels("Phenylketonuria")` → Newborn screening gene panels, PAH confirmed
5. **DiffDx** → differential for hyperphenylalaninaemia → PKU, BH4 deficiency, DHPR deficiency

### Model Interpretation Points

- Classic PKU confirmed (compound het R408W/P281L)
- Management: Phe-restricted diet, target Phe 2-6 mg/dL
- BH4 responsiveness: R408W typically non-responsive, but trial warranted given P281L may confer partial response
- Maternal PKU counseling for future pregnancies
- Long-term: neurocognitive monitoring, consider pegvaliase if adult diet adherence difficult

---

## Scenario 3: Duchenne Muscular Dystrophy — Neuromuscular

**Category**: Neuromuscular
**Complexity**: High — diagnostic odyssey, therapeutic decision

### Patient Presentation

> A 4-year-old boy is referred for progressive difficulty climbing stairs and a waddling gait. He uses a Gowers maneuver to stand from the floor. CK is markedly elevated at 15,000 U/L (normal <200). Family history is negative. Genetic testing reveals a deletion of exons 45-50 in the DMD gene. Mother's testing confirms she is a carrier (deletion on one allele).

### Expected Tool Invocations

1. **Orphanet** → `search_disease("Duchenne muscular dystrophy")` → ORPHA:98896, X-linked recessive, incidence 1/3,500 male births
2. **PanelApp** → `search_panels("muscular dystrophy")` → Neuromuscular disease gene panels, DMD gene confirmed as GREEN (diagnostic grade)
3. **ClinVar** → `search_variant("exon 45-50 deletion", gene="DMD")` → Pathogenic, Duchenne muscular dystrophy, out-of-frame deletion
4. **PubMed** → `search("DMD exon skipping therapy 2025")` → Eteplirsen (exon 51 skip), casimersen (exon 45), recent gene therapy trials
5. **HPO** → `search_term("Gowers sign")` → HP:0003391, characteristic of proximal muscle weakness

### Model Interpretation Points

- DMD confirmed: exon 45-50 deletion is out-of-frame → Duchenne (not Becker)
- Exon skipping eligibility: deletion of 45-50 is amenable to exon 44 skipping (golodirsen)
- Standard of care: corticosteroids (deflazacort), cardiac monitoring, pulmonary function testing
- Anticipatory guidance: loss of ambulation typically by age 10-12
- Carrier mother: 50% risk for future male offspring, genetic counseling critical

---

## Scenario 4: Ehlers-Danlos Syndrome (Vascular Type) — Connective Tissue

**Category**: Connective Tissue
**Complexity**: High — life-threatening, diagnostic precision critical

### Patient Presentation

> A 32-year-old woman presents to the ED with sudden severe abdominal pain. CT reveals a spontaneous splenic artery dissection. She has a history of easy bruising, translucent skin, and a sigmoid colon perforation at age 25. She has characteristic facial features (thin lips, small chin, prominent eyes). Family history reveals her father died suddenly at age 42 from aortic rupture. Genetic testing identifies a heterozygous c.2411G>A (G804D) variant in COL3A1.

### Expected Tool Invocations

1. **Orphanet** → `search_disease("Ehlers-Danlos syndrome vascular")` → ORPHA:286, autosomal dominant, prevalence 1/50,000-200,000
2. **ClinVar** → `search_variant("c.2411G>A", gene="COL3A1")` → Pathogenic, vascular EDS (glycine substitution in triple helix domain)
3. **DiffDx** → differential for arterial dissection + colon perforation + skin translucency → vascular EDS, Loeys-Dietz, Marfan
4. **PubMed** → `search("vascular Ehlers-Danlos COL3A1 management guidelines")` → Celiprolol trial, surveillance protocols, surgical risk
5. **PanelApp** → `search_panels("aortic disease")` → Aortopathy gene panels, COL3A1 confirmed

### Model Interpretation Points

- Vascular EDS (Type IV) confirmed: COL3A1 glycine substitution = classical pathogenic mechanism
- CRITICAL: Major 2023 Villefranche criteria met (spontaneous arterial dissection, bowel rupture, characteristic facies)
- Management: celiprolol (beta-blocker with evidence in vEDS), avoid invasive procedures when possible
- Surveillance: annual vascular imaging, avoid contact sports and isometric exercise
- Family screening: 50% risk for children, presymptomatic genetic testing recommended

---

## Scenario 5: Severe Combined Immunodeficiency (SCID) — Immunodeficiency

**Category**: Immunodeficiency
**Complexity**: High — newborn emergency, treatment decision

### Patient Presentation

> A 3-month-old male presents with persistent oral thrush, failure to thrive, and Pneumocystis jirovecii pneumonia. Newborn screening TREC assay was abnormal (TRECs <25 copies/µL). Flow cytometry shows absent T cells (CD3+ <300/µL), present but non-functional B cells, and absent NK cells. The T-B+NK- SCID phenotype suggests an IL2RG or JAK3 defect. Genetic testing reveals a hemizygous c.690C>A (C229X) nonsense variant in IL2RG (X-linked).

### Expected Tool Invocations

1. **Orphanet** → `search_disease("X-linked severe combined immunodeficiency")` → ORPHA:276, X-linked recessive, most common SCID subtype (~45%)
2. **ClinVar** → `search_variant("c.690C>A", gene="IL2RG")` → Pathogenic, X-SCID, nonsense mutation → null gamma chain
3. **PanelApp** → `search_panels("primary immunodeficiency")` → SCID gene panels, IL2RG confirmed as GREEN
4. **PubMed** → `search("IL2RG SCID gene therapy lentiviral 2025")` → Lentiviral gene therapy trials, HCT outcomes
5. **HPO** → `search_term("T-cell lymphopenia")` → HP:0005403, SCID subtypes and immunodeficiency spectrum

### Model Interpretation Points

- X-SCID confirmed: IL2RG nonsense mutation → absent gamma chain → no IL-2/4/7/9/15/21 signaling
- URGENT: This is a pediatric emergency — protective isolation and antimicrobial prophylaxis immediately
- Treatment options: (1) HCT from matched sibling (best outcomes), (2) Haploidentical HCT, (3) Gene therapy (clinical trials)
- Prognosis: Without treatment, fatal within first year. With early HCT, >90% survival
- Mother is obligate carrier — genetic counseling for future pregnancies, prenatal testing available

---

## Scenario 6: MELAS Syndrome — IEM/Mitochondrial

**Category**: Inborn Errors of Metabolism (Mitochondrial)
**Complexity**: High — multisystem, variable phenotype

### Patient Presentation

> A 19-year-old woman presents with recurrent migraine-like headaches, seizures, and acute-onset left hemiparesis. MRI shows stroke-like lesions in the occipital and temporal lobes that do not follow vascular territories. Serum lactate is elevated at 4.2 mmol/L (normal <2.0). She has sensorineural hearing loss and short stature. Muscle biopsy shows ragged red fibers. Mitochondrial DNA testing reveals the m.3243A>G variant in MT-TL1 with 65% heteroplasmy in muscle.

### Expected Tool Invocations

1. **Orphanet** → `search_disease("MELAS syndrome")` → ORPHA:550, maternal inheritance, prevalence 1/4,000
2. **ClinVar** → `search_variant("m.3243A>G", gene="MT-TL1")` → Pathogenic, MELAS/MIDD, most common MELAS variant (>80%)
3. **DiffDx** → differential for stroke-like episodes + lactic acidosis + hearing loss → MELAS, MERRF, Leigh syndrome, Kearns-Sayre
4. **PubMed** → `search("MELAS m.3243A>G treatment arginine 2025")` → L-arginine (acute and chronic), CoQ10, seizure management
5. **HPO** → `search_term("stroke-like episode")` → HP:0002401, mitochondrial spectrum

### Model Interpretation Points

- MELAS confirmed: m.3243A>G (MT-TL1) at 65% heteroplasmy — above typical symptom threshold (~60-70%)
- Heteroplasmy level matters: lower in blood (may underestimate), muscle biopsy is gold standard
- Management: L-arginine (vasodilation for stroke-like episodes), CoQ10 supplementation, avoid valproate (mitochondrial toxicity)
- Avoid: fasting, high-intensity exercise, aminoglycosides
- Maternal inheritance: all maternal relatives at risk (variable heteroplasmy = variable phenotype)
- Screen for: diabetes (MIDD), cardiomyopathy, nephropathy

---

## Scenario 7: Common Variable Immunodeficiency (CVID) — Immunodeficiency

**Category**: Immunodeficiency
**Complexity**: Moderate — chronic presentation

### Patient Presentation

> A 28-year-old woman is referred after her fourth episode of bacterial pneumonia in two years. She has a history of chronic sinusitis since childhood and one episode of Giardia enteritis. Immunoglobulin levels show IgG 280 mg/dL (normal 700-1,600), IgA <7 mg/dL, and IgM 35 mg/dL. Vaccine responses to pneumococcal polysaccharide are absent despite vaccination. B cells are present but memory B cells (CD27+) are markedly reduced. Genetic testing reveals a heterozygous pathogenic variant in TNFRSF13B (TACI): c.310T>C (C104R).

### Expected Tool Invocations

1. **Orphanet** → `search_disease("Common variable immunodeficiency")` → ORPHA:1572, most common symptomatic primary immunodeficiency (1/25,000-50,000)
2. **ClinVar** → `search_variant("c.310T>C", gene="TNFRSF13B")` → Pathogenic/risk factor, CVID susceptibility (incomplete penetrance)
3. **PanelApp** → `search_panels("primary immunodeficiency")` → Antibody deficiency panels, TNFRSF13B included
4. **PubMed** → `search("CVID immunoglobulin replacement therapy monitoring")` → IgG replacement (IV or SC), trough level targets, infection reduction
5. **Orphanet** → `get_disease_phenotypes("1572")` → Phenotype spectrum: infections, autoimmunity, granulomatous disease, lymphoid malignancy

### Model Interpretation Points

- CVID confirmed: hypogammaglobulinemia + absent vaccine responses + recurrent infections after age 4
- TACI variant: incomplete penetrance (many carriers unaffected) — genetic counseling nuanced
- Management: lifelong IgG replacement therapy, target trough IgG >500-700 mg/dL
- Complications to monitor: autoimmune cytopenias (20%), granulomatous disease (8-22%), lymphoma (5-8%)
- Important: rule out secondary causes (medications, protein-losing enteropathy, lymphoproliferation)

---

## Scenario 8: Wilson Disease — IEM

**Category**: Inborn Errors of Metabolism
**Complexity**: Moderate — classic metabolic with neuropsychiatric features

### Patient Presentation

> A 16-year-old male presents with declining school performance, personality changes, and a new tremor. Slit-lamp exam reveals golden-brown Kayser-Fleischer rings. Labs show low ceruloplasmin (8 mg/dL, normal 20-40), elevated 24-hour urine copper (180 µg/day, normal <40), and mildly elevated transaminases. Liver biopsy shows hepatic copper content of 320 µg/g dry weight (normal <50). Genetic testing reveals compound heterozygous variants in ATP7B: c.3207C>A (H1069Q) and c.2333G>T (R778L).

### Expected Tool Invocations

1. **Orphanet** → `search_disease("Wilson disease")` → ORPHA:905, autosomal recessive, prevalence 1/30,000
2. **ClinVar** → `search_variant("c.3207C>A", gene="ATP7B")` → Pathogenic, Wilson disease, H1069Q most common European variant
3. **ClinVar** → `search_variant("c.2333G>T", gene="ATP7B")` → Pathogenic, Wilson disease, R778L most common East Asian variant
4. **gnomAD** → `query_variant("13-51421838-G-T")` → H1069Q carrier frequency ~1/90 in Europeans
5. **PubMed** → `search("Wilson disease ATP7B chelation therapy penicillamine trientine")` → Chelation (penicillamine, trientine) vs zinc maintenance

### Model Interpretation Points

- Wilson disease confirmed: Leipzig score >4 (KF rings + low ceruloplasmin + elevated urinary copper + high hepatic copper + two pathogenic ATP7B variants)
- Interesting genotype: European (H1069Q) + East Asian (R778L) compound het — mixed ancestry or de novo
- Treatment: initial chelation with trientine (preferred over penicillamine for neurologic presentation), transition to zinc maintenance
- Neuropsychiatric Wilson can worsen initially with chelation — close monitoring
- Screen siblings: 25% risk, presymptomatic treatment prevents organ damage
- Dietary copper restriction (avoid shellfish, liver, chocolate, mushrooms)

---

## Scenario 9: Fabry Disease — IEM/Lysosomal Storage

**Category**: Inborn Errors of Metabolism
**Complexity**: High — late-onset, often missed

### Patient Presentation

> A 38-year-old man presents with progressive renal failure (GFR 45 mL/min), left ventricular hypertrophy (septum 16mm) without hypertension, and a history of childhood acroparesthesias (burning pain in hands/feet with fevers). He has clustered angiokeratomas on his trunk and cornea verticillata on slit-lamp exam. Alpha-galactosidase A enzyme activity is low at 0.8 nmol/hr/mL (normal >3.0). Genetic testing reveals a hemizygous c.644A>G (N215S) variant in GLA.

### Expected Tool Invocations

1. **Orphanet** → `search_disease("Fabry disease")` → ORPHA:324, X-linked, incidence 1/40,000-117,000
2. **ClinVar** → `search_variant("c.644A>G", gene="GLA")` → Pathogenic, Fabry disease, N215S associated with later-onset cardiac/renal phenotype
3. **DiffDx** → differential for LVH + renal failure + acroparesthesias → Fabry disease, hypertensive heart disease, amyloidosis
4. **PubMed** → `search("Fabry disease enzyme replacement therapy migalastat chaperone")` → ERT (agalsidase alfa/beta) vs oral chaperone (migalastat for amenable variants)
5. **Orphanet** → `get_disease_phenotypes("324")` → Full phenotype spectrum across organ systems

### Model Interpretation Points

- Fabry disease confirmed (classic male): low alpha-gal A + pathogenic GLA variant + characteristic phenotype
- N215S is amenable to migalastat (oral chaperone therapy) — check amenability table
- Renal management: ACEi/ARB for proteinuria, renal transplant evaluation if progression
- Cardiac: MRI for fibrosis assessment, annual echocardiography
- Family: X-linked — obligate carrier females may have attenuated symptoms (screen mother, sisters)
- This patient had a >20-year diagnostic delay (acroparesthesias at childhood → diagnosis at 38)

---

## Scenario 10: 22q11.2 Deletion Syndrome — Complex/Multi-System

**Category**: Complex Genetic (bonus — demonstrates breadth of tool pipeline)
**Complexity**: High — multisystem, variable expressivity

### Patient Presentation

> A 2-year-old girl is evaluated for recurrent infections and failure to thrive. She was born with a cleft palate (repaired at 9 months) and had neonatal hypocalcemia requiring NICU admission. Echocardiography at birth showed a right aortic arch and aberrant subclavian artery. Immunological workup shows low but present T cells with reduced thymic output (low TRECs). She has subtle facial dysmorphism (hooded eyelids, tubular nose). Chromosomal microarray reveals a 2.5 Mb deletion at 22q11.21.

### Expected Tool Invocations

1. **Orphanet** → `search_disease("22q11.2 deletion syndrome")` → ORPHA:567, most common microdeletion syndrome (1/4,000)
2. **HPO** → `search_term("velopharyngeal insufficiency")` → HP:0000220, spectrum of palatal anomalies in 22q11.2
3. **PanelApp** → `search_panels("22q11 deletion")` → Cardiac panels include TBX1 region, immunodeficiency panels
4. **PubMed** → `search("22q11.2 deletion syndrome psychiatric risk schizophrenia")` → 25-30% risk of psychotic disorder in adulthood
5. **DiffDx** → differential for cleft palate + cardiac defect + T-cell lymphopenia + hypocalcemia → 22q11.2 deletion (DiGeorge), CHARGE syndrome, Alagille syndrome

### Model Interpretation Points

- 22q11.2 deletion syndrome confirmed: classic presentation with CATCH-22 features (Cardiac, Abnormal facies, Thymic hypoplasia, Cleft palate, Hypocalcemia)
- Key gene: TBX1 in the deleted region drives most cardiac and pharyngeal features
- Immunological: partial DiGeorge (T cells present but reduced) — may improve with age, avoid live vaccines until T cells adequate
- Long-term surveillance: calcium monitoring, speech therapy, developmental assessment, psychiatric screening in adolescence
- De novo in >90% of cases — recurrence risk for parents is low, but 50% risk if the affected individual has children

---

## System Prompt — Rare Disease Specialist

The following system prompt is configured in OpenWebUI for the "Rare Disease Specialist" model preset:

```
You are a rare disease clinical genetics specialist with access to diagnostic tools. Your role is to assist clinicians in evaluating patients with suspected rare genetic conditions.

When presented with a patient case:

1. ANALYZE the clinical presentation systematically
2. GENERATE a differential diagnosis ranked by probability
3. USE your clinical tools to gather supporting evidence:
   - Orphanet: Disease information, prevalence, genetics
   - ClinVar: Variant pathogenicity classification
   - gnomAD: Population allele frequencies
   - PanelApp: Gene panels for the suspected condition
   - HPO: Map clinical features to HPO terms
   - PubMed: Recent literature on diagnosis and management
   - DiffDx: Structured differential diagnosis
4. SYNTHESIZE findings into a clinical assessment with:
   - Most likely diagnosis with supporting evidence
   - Key confirmatory findings
   - Differential diagnoses to consider
   - Recommended management and monitoring
   - Genetic counseling points
   - Red flags or urgent considerations

IMPORTANT GUIDELINES:
- Always state the evidence level for your recommendations
- Flag any findings that require urgent clinical action
- Note when clinical correlation is needed
- Acknowledge limitations and uncertainty
- Never provide a definitive diagnosis — frame as "findings consistent with" or "suggestive of"
- Include inheritance pattern and family implications
- Reference ACMG/AMP guidelines for variant interpretation when relevant

Use /no_think to skip internal reasoning and respond directly with clinical assessment.
```

### /no_think Behavior

When the user or system includes `/no_think` in the prompt:
- The model skips its extended thinking phase
- Response content appears in `content` field (not `reasoning_content`)
- Faster response time, suitable for tool-calling interactions
- Clinical assessment goes directly to the user without internal deliberation

### Tool Result Formatting

The model should format tool results inline as:

```
**[Orphanet]** Gaucher disease (ORPHA:355) — Type 1, non-neuropathic
  Prevalence: 1/57,000 (general), ~1/850 (Ashkenazi Jewish)
  Inheritance: Autosomal recessive (GBA1)
```

Not as raw JSON dumps. The model interprets and contextualizes each tool result before presenting it.

---

## Testing Checklist

For each scenario, verify:

- [ ] Model invokes the correct tools (not all — only clinically relevant ones)
- [ ] Tool results are returned without errors (API connectivity)
- [ ] Model synthesizes tool results into coherent clinical assessment
- [ ] No hallucinated tool results (model uses actual returned data)
- [ ] /no_think produces direct clinical output
- [ ] Response time acceptable (<30s including tool calls)
- [ ] Model acknowledges uncertainty appropriately
- [ ] Inheritance and family counseling included

### Quick Test Commands

```
# Scenario 1 — simple IEM
A 28-year-old Ashkenazi Jewish male with hepatosplenomegaly, thrombocytopenia, elevated chitotriosidase, and homozygous GBA1 N370S variant. What is the diagnosis and management?

# Scenario 3 — neuromuscular
A 4-year-old boy with Gowers sign, CK 15,000, and DMD exon 45-50 deletion. Assess diagnosis, exon skipping eligibility, and management.

# Scenario 5 — urgent SCID
A 3-month-old male with absent T cells, PJP pneumonia, and IL2RG C229X mutation. What is the diagnosis and how urgent is treatment?
```
