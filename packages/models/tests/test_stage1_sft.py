"""Tests for Stage 1 SFT config and data loading."""

import json
from unittest.mock import MagicMock

from rare_archive_models.training.stage1_sft import (
    SFTConfig,
    load_training_data,
    format_chat_template,
)


class TestSFTConfig:
    """Tests for SFTConfig dataclass."""

    def test_defaults(self):
        config = SFTConfig()
        assert config.model_name == "Qwen/Qwen3.5-4B"
        assert config.lora_rank == 64
        assert config.lora_alpha == 128
        assert config.max_seq_length == 4096
        assert config.bf16 is True

    def test_from_yaml(self, yaml_file):
        data = {"model_name": "Qwen/Qwen3.5-9B", "lora_rank": 32, "num_train_epochs": 5}
        path = yaml_file(data, "sft.yaml")
        config = SFTConfig.from_yaml(path)
        assert config.model_name == "Qwen/Qwen3.5-9B"
        assert config.lora_rank == 32
        assert config.num_train_epochs == 5

    def test_from_hierarchy(self, yaml_file, tmp_path):
        base = yaml_file({"model_name": "Qwen/Qwen3.5-4B", "lora_rank": 64}, "base.yaml")
        stage = yaml_file({"learning_rate": 1e-4, "num_train_epochs": 2}, "stage.yaml")
        category = yaml_file({"patient_category": "neuromuscular"}, "category.yaml")
        config = SFTConfig.from_hierarchy(base, stage, category)
        assert config.model_name == "Qwen/Qwen3.5-4B"
        assert config.learning_rate == 1e-4
        assert config.patient_category == "neuromuscular"


class TestLoadTrainingData:
    """Tests for load_training_data()."""

    def test_valid_jsonl(self, sample_training_records, jsonl_file):
        path = jsonl_file(sample_training_records, "train.jsonl")
        records = load_training_data(str(path))
        assert len(records) == 2
        assert "messages" in records[0]

    def test_max_samples_limit(self, sample_training_records, jsonl_file):
        path = jsonl_file(sample_training_records, "train.jsonl")
        records = load_training_data(str(path), max_samples=1)
        assert len(records) == 1

    def test_empty_file(self, tmp_path):
        path = tmp_path / "empty.jsonl"
        path.write_text("")
        records = load_training_data(str(path))
        assert records == []


class TestFormatChatTemplate:
    """Tests for format_chat_template()."""

    def test_applies_chat_template(self):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]
        tokenizer = MagicMock()
        tokenizer.apply_chat_template.return_value = "<|user|>Hello<|assistant|>Hi"
        result = format_chat_template(messages, tokenizer)
        assert result == "<|user|>Hello<|assistant|>Hi"
        tokenizer.apply_chat_template.assert_called_once_with(
            messages, tokenize=False, add_generation_prompt=False,
        )

    def test_fallback_when_no_template(self):
        """When tokenizer raises, the error propagates (no silent fallback)."""
        messages = [{"role": "user", "content": "test"}]
        tokenizer = MagicMock()
        tokenizer.apply_chat_template.side_effect = AttributeError("no template")
        try:
            format_chat_template(messages, tokenizer)
            assert False, "Should have raised"
        except AttributeError:
            pass
