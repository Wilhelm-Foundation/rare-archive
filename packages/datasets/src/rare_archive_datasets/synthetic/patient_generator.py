"""Synthetic patient generator for the Rare AI Archive.

Generates synthetic clinical vignettes from Orphanet/HPO disease profiles.
No real PHI — all patients are computationally generated.

Each synthetic patient includes:
- Demographics (age, sex, ethnicity — sampled from epidemiological distributions)
- Presenting symptoms (HPO terms with frequency-weighted sampling)
- Clinical history timeline
- Laboratory/imaging findings
- Family history (based on inheritance patterns)
"""

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DiseaseProfile:
    """A disease profile from which synthetic patients are generated."""
    disease_id: str
    disease_name: str
    ordo_id: str | None = None
    hpo_phenotypes: list[dict[str, Any]] = field(default_factory=list)
    inheritance_patterns: list[str] = field(default_factory=list)
    age_of_onset: list[str] = field(default_factory=list)
    prevalence: str | None = None
    patient_category: str | None = None


@dataclass
class SyntheticPatient:
    """A computationally generated patient case."""
    patient_id: str
    disease_profile: DiseaseProfile
    age: int
    sex: str
    presenting_symptoms: list[dict[str, str]]
    additional_findings: list[dict[str, str]]
    family_history: str
    clinical_vignette: str
    ground_truth_diagnosis: str
    hpo_terms_present: list[str]
    hpo_terms_absent: list[str]
    difficulty: str  # easy, medium, hard
    patient_category: str | None = None


# HPO frequency qualifiers mapped to sampling probabilities
FREQUENCY_PROBABILITIES = {
    "obligate": 1.0,
    "very_frequent": 0.9,
    "frequent": 0.55,
    "occasional": 0.17,
    "very_rare": 0.025,
    "excluded": 0.0,
}

# Age of onset HPO terms mapped to age ranges
AGE_ONSET_RANGES = {
    "HP:0003623": (0, 0),       # Neonatal onset
    "HP:0003593": (0, 1),       # Infantile onset
    "HP:0011463": (1, 5),       # Childhood onset
    "HP:0003621": (5, 15),      # Juvenile onset
    "HP:0003581": (16, 40),     # Adult onset
    "HP:0003584": (40, 80),     # Late onset
    "antenatal": (0, 0),
    "neonatal": (0, 0),
    "infantile": (0, 1),
    "childhood": (1, 12),
    "juvenile": (5, 15),
    "adult": (16, 60),
    "late": (40, 80),
}

SEX_OPTIONS = ["male", "female"]


def load_disease_profiles(profiles_path: Path) -> list[DiseaseProfile]:
    """Load disease profiles from a JSON/JSONL file."""
    profiles = []
    suffix = profiles_path.suffix.lower()

    if suffix == ".jsonl":
        with open(profiles_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    profiles.append(_parse_profile(data))
    elif suffix == ".json":
        with open(profiles_path) as f:
            data = json.load(f)
            if isinstance(data, list):
                profiles = [_parse_profile(d) for d in data]
            else:
                profiles = [_parse_profile(data)]

    return profiles


def _parse_profile(data: dict) -> DiseaseProfile:
    """Parse a disease profile from dict."""
    return DiseaseProfile(
        disease_id=data.get("disease_id", ""),
        disease_name=data.get("disease_name", data.get("name", "")),
        ordo_id=data.get("ordo_id"),
        hpo_phenotypes=data.get("hpo_phenotypes", data.get("phenotypes", [])),
        inheritance_patterns=data.get("inheritance_patterns", []),
        age_of_onset=data.get("age_of_onset", []),
        prevalence=data.get("prevalence"),
        patient_category=data.get("patient_category"),
    )


def generate_patient(
    profile: DiseaseProfile,
    patient_id: str,
    difficulty: str = "medium",
    rng: random.Random | None = None,
) -> SyntheticPatient:
    """Generate a single synthetic patient from a disease profile.

    Args:
        profile: Disease profile to generate from
        patient_id: Unique patient identifier
        difficulty: "easy" (many symptoms), "medium", "hard" (few symptoms, distractors)
        rng: Random number generator for reproducibility
    """
    if rng is None:
        rng = random.Random()

    # Sample demographics
    sex = rng.choice(SEX_OPTIONS)
    age = _sample_age(profile.age_of_onset, rng)

    # Sample symptoms based on HPO phenotype frequencies
    presenting, additional, present_hpo, absent_hpo = _sample_symptoms(
        profile.hpo_phenotypes, difficulty, rng
    )

    # Generate family history
    family_hx = _generate_family_history(profile.inheritance_patterns, rng)

    # Compose clinical vignette
    vignette = _compose_vignette(
        age=age,
        sex=sex,
        presenting=presenting,
        additional=additional,
        family_hx=family_hx,
        disease_name=profile.disease_name,
        difficulty=difficulty,
    )

    return SyntheticPatient(
        patient_id=patient_id,
        disease_profile=profile,
        age=age,
        sex=sex,
        presenting_symptoms=presenting,
        additional_findings=additional,
        family_history=family_hx,
        clinical_vignette=vignette,
        ground_truth_diagnosis=profile.disease_name,
        hpo_terms_present=present_hpo,
        hpo_terms_absent=absent_hpo,
        difficulty=difficulty,
        patient_category=profile.patient_category,
    )


def _sample_age(onset_terms: list[str], rng: random.Random) -> int:
    """Sample an age based on onset terms."""
    if not onset_terms:
        return rng.randint(1, 60)

    term = rng.choice(onset_terms)
    term_lower = term.lower()

    for key, (lo, hi) in AGE_ONSET_RANGES.items():
        if key in term_lower or term_lower in key:
            return rng.randint(lo, max(lo, hi))

    return rng.randint(1, 60)


def _sample_symptoms(
    phenotypes: list[dict],
    difficulty: str,
    rng: random.Random,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[str], list[str]]:
    """Sample symptoms from phenotype list based on difficulty."""
    presenting = []
    additional = []
    present_hpo = []
    absent_hpo = []

    # Difficulty affects how many symptoms are shown
    difficulty_modifier = {"easy": 1.3, "medium": 1.0, "hard": 0.6}
    modifier = difficulty_modifier.get(difficulty, 1.0)

    for pheno in phenotypes:
        hpo_id = pheno.get("hpo_id", "")
        term = pheno.get("term", pheno.get("name", ""))
        freq = pheno.get("frequency", "frequent")

        base_prob = FREQUENCY_PROBABILITIES.get(freq, 0.5)
        adjusted_prob = min(1.0, base_prob * modifier)

        if rng.random() < adjusted_prob:
            symptom = {"hpo_id": hpo_id, "term": term}
            if base_prob >= 0.5:
                presenting.append(symptom)
            else:
                additional.append(symptom)
            present_hpo.append(hpo_id)
        else:
            absent_hpo.append(hpo_id)

    return presenting, additional, present_hpo, absent_hpo


def _generate_family_history(
    inheritance: list[str],
    rng: random.Random,
) -> str:
    """Generate a family history string based on inheritance patterns."""
    if not inheritance:
        return "No significant family history reported."

    pattern = inheritance[0].lower()

    templates = {
        "autosomal_dominant": [
            "Father has similar symptoms. Paternal grandmother was also affected.",
            "Mother was diagnosed with the same condition at age {age}.",
            "Multiple family members across generations are affected.",
        ],
        "autosomal_recessive": [
            "Parents are consanguineous. No other affected family members.",
            "One sibling is similarly affected. Parents are unaffected carriers.",
            "No family history. Parents are from a small geographic community.",
        ],
        "x_linked": [
            "Maternal uncle has a similar condition. Mother is an unaffected carrier.",
            "Maternal grandfather was affected. Multiple maternal male relatives affected.",
        ],
        "mitochondrial": [
            "Mother and maternal siblings have variable symptoms.",
            "Maternal lineage shows multiple individuals with related symptoms.",
        ],
    }

    for key, options in templates.items():
        if key in pattern:
            template = rng.choice(options)
            return template.format(age=rng.randint(20, 50))

    return "Family history is non-contributory."


def _compose_vignette(
    age: int,
    sex: str,
    presenting: list[dict[str, str]],
    additional: list[dict[str, str]],
    family_hx: str,
    disease_name: str,
    difficulty: str,
) -> str:
    """Compose a clinical vignette from patient components."""
    age_desc = _age_description(age)
    pronoun = "He" if sex == "male" else "She"

    lines = [f"A {age}-year-old {sex} {age_desc} presents with:"]

    if presenting:
        symptoms = [s["term"] for s in presenting if s.get("term")]
        if symptoms:
            lines.append("- " + "\n- ".join(symptoms))

    if additional:
        lines.append(f"\nAdditional findings:")
        findings = [s["term"] for s in additional if s.get("term")]
        if findings:
            lines.append("- " + "\n- ".join(findings))

    lines.append(f"\nFamily history: {family_hx}")

    if difficulty != "easy":
        lines.append(f"\n{pronoun} has been evaluated by multiple specialists "
                     f"over the past {age // 4 + 1} years without a definitive diagnosis.")

    return "\n".join(lines)


def _age_description(age: int) -> str:
    """Human-readable age description."""
    if age < 1:
        return "neonate"
    elif age < 3:
        return "infant"
    elif age < 12:
        return "child"
    elif age < 18:
        return "adolescent"
    else:
        return ""


def generate_batch(
    profiles: list[DiseaseProfile],
    n_per_profile: int = 3,
    difficulties: list[str] | None = None,
    seed: int = 42,
) -> list[SyntheticPatient]:
    """Generate a batch of synthetic patients across disease profiles.

    Args:
        profiles: Disease profiles to generate from
        n_per_profile: Number of patients per profile
        difficulties: List of difficulty levels to cycle through
        seed: Random seed for reproducibility
    """
    if difficulties is None:
        difficulties = ["easy", "medium", "hard"]

    rng = random.Random(seed)
    patients = []

    for profile in profiles:
        for i in range(n_per_profile):
            difficulty = difficulties[i % len(difficulties)]
            patient_id = f"synth_{profile.disease_id}_{i:03d}"
            patient = generate_patient(profile, patient_id, difficulty, rng)
            patients.append(patient)

    return patients


def export_patients(
    patients: list[SyntheticPatient],
    output_path: Path,
) -> int:
    """Export synthetic patients as JSONL."""
    count = 0
    with open(output_path, "w", encoding="utf-8") as f:
        for patient in patients:
            record = {
                "patient_id": patient.patient_id,
                "clinical_vignette": patient.clinical_vignette,
                "ground_truth_diagnosis": patient.ground_truth_diagnosis,
                "disease_id": patient.disease_profile.disease_id,
                "hpo_terms_present": patient.hpo_terms_present,
                "hpo_terms_absent": patient.hpo_terms_absent,
                "age": patient.age,
                "sex": patient.sex,
                "difficulty": patient.difficulty,
                "patient_category": patient.patient_category,
                "family_history": patient.family_history,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1

    return count
