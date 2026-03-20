"""Tests for synthetic patient generator."""

import json
import random

import pytest

from rare_archive_datasets.synthetic.patient_generator import (
    DiseaseProfile,
    SyntheticPatient,
    _age_description,
    _compose_vignette,
    _generate_family_history,
    _sample_age,
    _sample_symptoms,
    export_patients,
    generate_batch,
    generate_patient,
    load_disease_profiles,
)


class TestLoadDiseaseProfiles:
    def test_json_list(self, tmp_path):
        data = [
            {"disease_id": "D1", "name": "Disease 1"},
            {"disease_id": "D2", "name": "Disease 2"},
        ]
        f = tmp_path / "profiles.json"
        f.write_text(json.dumps(data))
        profiles = load_disease_profiles(f)
        assert len(profiles) == 2
        assert profiles[0].disease_name == "Disease 1"

    def test_json_single_object(self, tmp_path):
        data = {"disease_id": "D1", "disease_name": "Disease 1"}
        f = tmp_path / "profile.json"
        f.write_text(json.dumps(data))
        profiles = load_disease_profiles(f)
        assert len(profiles) == 1

    def test_jsonl(self, tmp_path):
        f = tmp_path / "profiles.jsonl"
        f.write_text('{"disease_id":"D1","name":"D1 Name"}\n{"disease_id":"D2","name":"D2 Name"}\n')
        profiles = load_disease_profiles(f)
        assert len(profiles) == 2

    def test_field_parsing_with_fallback_keys(self, tmp_path):
        data = {
            "disease_id": "D1",
            "name": "FallbackName",
            "phenotypes": [{"hpo_id": "HP:0001"}],
        }
        f = tmp_path / "profile.json"
        f.write_text(json.dumps(data))
        profiles = load_disease_profiles(f)
        assert profiles[0].disease_name == "FallbackName"
        assert profiles[0].hpo_phenotypes == [{"hpo_id": "HP:0001"}]


class TestGeneratePatient:
    def test_returns_synthetic_patient(self, disease_profile):
        patient = generate_patient(disease_profile, "p001", rng=random.Random(42))
        assert isinstance(patient, SyntheticPatient)

    def test_deterministic_with_seeded_rng(self, disease_profile):
        p1 = generate_patient(disease_profile, "p001", rng=random.Random(42))
        p2 = generate_patient(disease_profile, "p001", rng=random.Random(42))
        assert p1.age == p2.age
        assert p1.sex == p2.sex
        assert p1.clinical_vignette == p2.clinical_vignette

    def test_ground_truth_equals_profile_name(self, disease_profile):
        patient = generate_patient(disease_profile, "p001", rng=random.Random(42))
        assert patient.ground_truth_diagnosis == "Marfan syndrome"

    def test_sex_is_valid(self, disease_profile):
        patient = generate_patient(disease_profile, "p001", rng=random.Random(42))
        assert patient.sex in ["male", "female"]

    def test_difficulty_propagated(self, disease_profile):
        patient = generate_patient(disease_profile, "p001", difficulty="hard", rng=random.Random(42))
        assert patient.difficulty == "hard"


class TestSampleAge:
    def test_childhood_onset(self):
        for seed in range(20):
            age = _sample_age(["childhood"], random.Random(seed))
            assert 1 <= age <= 12

    def test_adult_onset(self):
        for seed in range(20):
            age = _sample_age(["adult"], random.Random(seed))
            assert 16 <= age <= 60

    def test_empty_onset_fallback(self):
        for seed in range(20):
            age = _sample_age([], random.Random(seed))
            assert 1 <= age <= 60


class TestSampleSymptoms:
    def test_obligate_always_present(self):
        phenotypes = [
            {"hpo_id": "HP:0001166", "term": "Arachnodactyly", "frequency": "obligate"},
        ]
        for seed in range(20):
            _, _, present, _ = _sample_symptoms(phenotypes, "medium", random.Random(seed))
            assert "HP:0001166" in present

    def test_excluded_never_present(self):
        phenotypes = [
            {"hpo_id": "HP:0002996", "term": "Limited elbow extension", "frequency": "excluded"},
        ]
        for seed in range(20):
            _, _, present, _ = _sample_symptoms(phenotypes, "medium", random.Random(seed))
            assert "HP:0002996" not in present


class TestGenerateFamilyHistory:
    def test_autosomal_dominant(self):
        result = _generate_family_history(["autosomal_dominant"], random.Random(42))
        assert isinstance(result, str)
        assert len(result) > 0
        assert "non-contributory" not in result.lower()
        assert "no significant" not in result.lower()

    def test_empty_inheritance(self):
        result = _generate_family_history([], random.Random(42))
        assert result == "No significant family history reported."

    def test_unknown_pattern(self):
        result = _generate_family_history(["unknown_pattern_xyz"], random.Random(42))
        assert result == "Family history is non-contributory."


class TestComposeVignette:
    def test_contains_age_and_sex(self):
        vignette = _compose_vignette(
            age=8, sex="male",
            presenting=[{"term": "Seizures"}],
            additional=[], family_hx="None",
            disease_name="Epilepsy", difficulty="easy",
        )
        assert "8-year-old" in vignette
        assert "male" in vignette

    def test_specialist_line_by_difficulty(self):
        easy = _compose_vignette(
            age=8, sex="male",
            presenting=[{"term": "Seizures"}],
            additional=[], family_hx="None",
            disease_name="Epilepsy", difficulty="easy",
        )
        medium = _compose_vignette(
            age=8, sex="male",
            presenting=[{"term": "Seizures"}],
            additional=[], family_hx="None",
            disease_name="Epilepsy", difficulty="medium",
        )
        assert "specialists" not in easy
        assert "specialists" in medium


class TestAgeDescription:
    def test_neonate(self):
        assert _age_description(0) == "neonate"

    def test_infant(self):
        assert _age_description(2) == "infant"

    def test_child(self):
        assert _age_description(8) == "child"

    def test_adult(self):
        assert _age_description(30) == ""


class TestGenerateBatch:
    def test_correct_count(self):
        profiles = [
            DiseaseProfile(disease_id="D1", disease_name="Disease 1"),
            DiseaseProfile(disease_id="D2", disease_name="Disease 2"),
        ]
        patients = generate_batch(profiles, n_per_profile=3)
        assert len(patients) == 6

    def test_difficulty_cycling(self):
        profile = DiseaseProfile(disease_id="D1", disease_name="Disease 1")
        patients = generate_batch([profile], n_per_profile=3)
        assert patients[0].difficulty == "easy"
        assert patients[1].difficulty == "medium"
        assert patients[2].difficulty == "hard"

    def test_patient_id_format(self):
        profile = DiseaseProfile(disease_id="D1", disease_name="Disease 1")
        patients = generate_batch([profile], n_per_profile=2)
        assert patients[0].patient_id == "synth_D1_000"
        assert patients[1].patient_id == "synth_D1_001"


class TestExportPatients:
    def test_writes_jsonl_with_correct_count(self, disease_profile, tmp_path):
        patients = generate_batch([disease_profile], n_per_profile=3)
        out = tmp_path / "patients.jsonl"
        count = export_patients(patients, out)
        assert count == 3
        lines = [line for line in out.read_text().splitlines() if line.strip()]
        assert len(lines) == 3

    def test_exported_records_have_required_fields(self, disease_profile, tmp_path):
        patients = generate_batch([disease_profile], n_per_profile=1)
        out = tmp_path / "patients.jsonl"
        export_patients(patients, out)
        record = json.loads(out.read_text().strip())
        required = {
            "patient_id", "clinical_vignette", "ground_truth_diagnosis",
            "disease_id", "age", "sex", "difficulty",
        }
        assert required.issubset(set(record.keys()))
