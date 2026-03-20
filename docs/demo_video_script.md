# Rare AI Archive — Demo Video Script

**Duration target**: 4-5 minutes
**Format**: Screen recording (D2 decision: authentic over animated)
**Primary scenario**: Scenario 1 — Gaucher Disease (IEM)
**Recording options**:
- **Option A (Public)**: HuggingFace Space walkthrough → recommended for general audience
- **Option B (Board)**: L2 OpenWebUI live inference → recommended for Wilhelm Foundation board, shows full system

---

## Pre-Recording Checklist

- [ ] HF Space is live and responsive: `huggingface.co/spaces/Wilhelm-Foundation/rare-archive-clinical-demo`
- [ ] Browser clean (no personal tabs, bookmarks hidden)
- [ ] Screen resolution: 1920x1080 or 2560x1440
- [ ] Recording tool ready (QuickTime / OBS / Loom)
- [ ] Audio: quiet room, external mic preferred
- [ ] Close notifications (Do Not Disturb on)

---

## Script

### 0:00-0:20 — Title Card

**[Screen]**: GitHub repo landing page → scroll to show badges + README header

**[Voice]**: "Three hundred million people worldwide live with a rare disease. The average time to diagnosis is five to seven years. The Rare AI Archive is an open-source project building AI models to help close that gap."

### 0:20-0:45 — The Problem

**[Screen]**: Scroll to "How It Works" mermaid diagram in README

**[Voice]**: "We fine-tune language models on sixty-three thousand clinical vignettes covering thousands of rare diseases. The models learn to reason through clinical presentations, query specialized databases, and produce structured diagnostic assessments — the same workflow a clinical geneticist follows."

### 0:45-1:15 — Navigate to Demo

**[Screen]**: Click HuggingFace Space link → Space loads

**[Voice]**: "Let me show you how it works. This is our interactive demo on HuggingFace — anyone can try this, no account required."

### 1:15-2:30 — Scenario 1: Gaucher Disease

**[Screen]**: Select "Gaucher Disease" from dropdown → patient presentation appears

**[Voice]**: "Here's a clinical scenario. A twenty-eight-year-old Ashkenazi Jewish male presents with fatigue, easy bruising, and hepatosplenomegaly. Labs show thrombocytopenia and elevated chitotriosidase. Genetic testing reveals a homozygous N370S variant in GBA1."

**[Screen]**: Expand "Clinical Tool Results" accordion

**[Voice]**: "The model queries five specialized databases. Orphanet confirms Gaucher disease type one — the non-neuropathic form. ClinVar classifies the variant as pathogenic. gnomAD shows this variant has a carrier frequency of one in fifteen in the Ashkenazi Jewish population — a well-known founder effect."

**[Screen]**: Scroll down to clinical assessment

**[Voice]**: "Then it synthesizes everything into a structured clinical assessment. Diagnosis confirmed, key evidence cited, treatment options — enzyme replacement therapy or substrate reduction — and genetic counseling points. Notice it flags GBA1 heterozygosity as a Parkinson disease risk factor. That's the kind of connection that can take years to surface in a traditional diagnostic odyssey."

### 2:30-3:15 — Quick Tour of Other Scenarios

**[Screen]**: Click through 2-3 more scenarios (SCID, Fabry, 22q11.2)

**[Voice]**: "We have ten scenarios across six disease categories. Here's a pediatric emergency — X-linked SCID in a three-month-old. The model correctly flags this as time-critical and recommends protective isolation before treatment planning."

**[Voice]**: "And here — Fabry disease diagnosed at age thirty-eight. A twenty-year diagnostic delay. The model identifies migalastat eligibility based on the specific GLA variant. That's precision medicine driven by variant-level evidence."

### 3:15-3:45 — Architecture & Models

**[Screen]**: Switch to "About" tab

**[Voice]**: "The system uses seven clinical tool adapters — Orphanet, ClinVar, gnomAD, PanelApp, HPO, PubMed, and a differential diagnosis engine. Our four-B model is published on HuggingFace as a GGUF — you can run it locally on a laptop with llama.cpp. A thirty-five-billion parameter model is currently training."

### 3:45-4:15 — Getting Involved

**[Screen]**: Navigate to GitHub Discussions page → show welcome post

**[Voice]**: "This is an open-source project and we're actively looking for contributors — clinicians for evaluation, ML engineers for training pipeline improvements, bioinformaticians for data expansion. Check out the contributing guide or start a discussion."

### 4:15-4:30 — Close

**[Screen]**: Back to GitHub README → show "Built by people who believe that no disease is too rare to matter"

**[Voice]**: "The Rare AI Archive. Open-source AI for rare disease diagnostics. Links in the description."

---

## Post-Recording

- [ ] Trim dead air at start/end
- [ ] Add text overlay for title card if QuickTime (no built-in text)
- [ ] Export as MP4 1080p
- [ ] Upload: YouTube (unlisted) or GitHub Release attachment
- [ ] Add link to README and HF org page

---

## Notes

- Keep mouse movements deliberate and slow — viewers need to follow
- Pause briefly after selecting each scenario to let the UI render
- Don't read the clinical text verbatim — paraphrase naturally
- If using Option B (L2 live inference), ensure tunnel is up and model is loaded before recording
- Target audience: Wilhelm Foundation board members, potential clinical collaborators, HF community
