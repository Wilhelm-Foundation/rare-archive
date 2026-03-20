"""Shared fixtures for models package tests."""

import json
import textwrap
from pathlib import Path

import pytest


@pytest.fixture
def sample_config_dict():
    """Minimal SFT config as a dict (YAML-equivalent)."""
    return {
        "model_name": "Qwen/Qwen3.5-4B",
        "model_size": "4b",
        "architecture": "dense",
        "lora_rank": 64,
        "lora_alpha": 128,
        "max_seq_length": 4096,
        "num_train_epochs": 3,
        "learning_rate": 2e-4,
        "train_data": "data/train.jsonl",
        "output_dir": "outputs/test",
    }


@pytest.fixture
def sample_training_records():
    """Sample JSONL training records in chat format."""
    return [
        {
            "messages": [
                {"role": "system", "content": "You are a rare disease diagnostician."},
                {"role": "user", "content": "Patient presents with progressive muscle weakness."},
                {"role": "assistant", "content": "Based on the presentation, I suspect Duchenne muscular dystrophy."},
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "You are a rare disease diagnostician."},
                {"role": "user", "content": "Patient with recurrent fevers and rash."},
                {"role": "assistant", "content": "Consider familial Mediterranean fever."},
            ]
        },
    ]


@pytest.fixture
def sample_eval_cases():
    """Sample JSONL evaluation cases."""
    return [
        {
            "case_id": "CASE001",
            "clinical_vignette": "3-year-old with progressive proximal muscle weakness, calf pseudohypertrophy, elevated CK.",
            "ground_truth_diagnosis": "Duchenne muscular dystrophy",
            "disease_id": "ORPHA:98896",
            "patient_category": "neuromuscular",
        },
        {
            "case_id": "CASE002",
            "clinical_vignette": "Infant with hepatomegaly, hypoglycemia, lactic acidosis.",
            "ground_truth_diagnosis": "Glycogen storage disease type I",
            "disease_id": "ORPHA:364",
            "patient_category": "metabolic",
        },
    ]


@pytest.fixture
def sample_preference_pairs():
    """Sample DPO preference pairs."""
    return [
        {
            "prompt": "Patient with progressive ataxia and oculomotor apraxia.",
            "chosen": "This presentation is consistent with ataxia-telangiectasia.",
            "rejected": "The patient has a common cold.",
            "metadata": {"expert_id": "expert_001", "patient_category": "neurological"},
        },
        {
            "prompt": "Child with ichthyosis and intellectual disability.",
            "chosen": "Consider Sjögren-Larsson syndrome.",
            "rejected": "This is likely eczema.",
            "metadata": {"expert_id": "expert_002", "patient_category": "dermatological"},
        },
    ]


@pytest.fixture
def sample_model_response():
    """Sample numbered diagnosis response from a model."""
    return textwrap.dedent("""\
        1. Duchenne muscular dystrophy
        2. Becker muscular dystrophy
        3. Limb-girdle muscular dystrophy
        4. Spinal muscular atrophy
        5. Congenital myopathy
    """)


@pytest.fixture
def sample_baseline_results():
    """Baseline evaluation results (e.g., from GPT-4o)."""
    return {
        "top_1_accuracy": 0.65,
        "top_5_accuracy": 0.85,
        "mean_score": 1.45,
        "n_cases": 100,
    }


@pytest.fixture
def sample_current_results():
    """Current model evaluation results."""
    return {
        "top_1_accuracy": 0.64,
        "top_5_accuracy": 0.84,
        "mean_score": 1.40,
        "n_cases": 100,
    }


@pytest.fixture
def jsonl_file(tmp_path):
    """Factory fixture to create temp JSONL files."""
    def _create(records, filename="data.jsonl"):
        path = tmp_path / filename
        with open(path, "w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")
        return path
    return _create


@pytest.fixture
def yaml_file(tmp_path):
    """Factory fixture to create temp YAML files."""
    def _create(data, filename="config.yaml"):
        import yaml
        path = tmp_path / filename
        with open(path, "w") as f:
            yaml.dump(data, f)
        return path
    return _create
