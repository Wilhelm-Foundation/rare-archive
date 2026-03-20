"""Tests for Stage 3 DPO/GRPO config and data loading."""

from rare_archive_models.training.stage3_dpo import (
    DPOConfig,
    load_preference_pairs,
)


class TestDPOConfig:
    """Tests for DPOConfig dataclass."""

    def test_defaults(self):
        config = DPOConfig()
        assert config.method == "dpo"
        assert config.beta == 0.1
        assert config.loss_type == "sigmoid"
        assert config.lora_rank == 32
        assert config.lora_alpha == 64

    def test_from_yaml(self, yaml_file):
        data = {"method": "grpo", "beta": 0.2, "loss_type": "hinge"}
        path = yaml_file(data, "dpo.yaml")
        config = DPOConfig.from_yaml(path)
        assert config.method == "grpo"
        assert config.beta == 0.2
        assert config.loss_type == "hinge"


class TestLoadPreferencePairs:
    """Tests for load_preference_pairs()."""

    def test_valid_jsonl(self, sample_preference_pairs, jsonl_file):
        path = jsonl_file(sample_preference_pairs, "prefs.jsonl")
        pairs = load_preference_pairs(path)
        assert len(pairs) == 2
        assert "prompt" in pairs[0]
        assert "chosen" in pairs[0]
        assert "rejected" in pairs[0]

    def test_metadata_preserved(self, sample_preference_pairs, jsonl_file):
        path = jsonl_file(sample_preference_pairs, "prefs.jsonl")
        pairs = load_preference_pairs(path)
        assert pairs[0]["metadata"]["expert_id"] == "expert_001"
        assert pairs[0]["metadata"]["patient_category"] == "neurological"

    def test_empty_file(self, tmp_path):
        path = tmp_path / "empty.jsonl"
        path.write_text("")
        pairs = load_preference_pairs(path)
        assert pairs == []
