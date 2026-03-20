"""Tests for Stage 2 Tool-Use SFT."""

import json

from rare_archive_models.training.stage2_tool_use import (
    TOOL_DEFINITIONS,
    ToolUseSFTConfig,
    generate_tool_trace,
)


class TestToolDefinitions:
    """Tests for TOOL_DEFINITIONS constant."""

    def test_all_seven_tools_present(self):
        assert len(TOOL_DEFINITIONS) == 7
        names = {t["function"]["name"] for t in TOOL_DEFINITIONS}
        expected = {
            "clinvar_lookup", "orphanet_search", "hpo_lookup",
            "panelapp_search", "gnomad_lookup", "pubmed_search",
            "differential_diagnosis",
        }
        assert names == expected

    def test_tools_have_valid_schema(self):
        for tool in TOOL_DEFINITIONS:
            func = tool["function"]
            assert "name" in func
            assert "description" in func
            assert "parameters" in func
            params = func["parameters"]
            assert params["type"] == "object"
            assert "properties" in params
            assert "required" in params


class TestGenerateToolTrace:
    """Tests for generate_tool_trace()."""

    def test_returns_list_of_messages(self):
        case = {
            "clinical_vignette": "Patient with ataxia.",
            "ground_truth_diagnosis": "Friedreich ataxia",
        }
        tool_responses = {}
        messages = generate_tool_trace(case, tool_responses)
        assert isinstance(messages, list)
        assert all(isinstance(m, dict) for m in messages)

    def test_contains_tool_calls(self):
        case = {
            "clinical_vignette": "Patient with muscle weakness.",
            "ground_truth_diagnosis": "DMD",
        }
        tool_responses = {
            "hpo": {"query": "muscle weakness", "result": {"terms": ["HP:0001324"]}},
        }
        messages = generate_tool_trace(case, tool_responses)
        tool_call_msgs = [m for m in messages if "tool_calls" in m]
        assert len(tool_call_msgs) >= 1
        assert tool_call_msgs[0]["tool_calls"][0]["function"]["name"] == "hpo_lookup"

    def test_ends_with_assistant_synthesis(self):
        case = {
            "clinical_vignette": "Patient with symptoms.",
            "ground_truth_diagnosis": "Rare disease X",
        }
        messages = generate_tool_trace(case, {})
        last = messages[-1]
        assert last["role"] == "assistant"
        assert "Rare disease X" in last["content"]


class TestToolUseSFTConfig:
    """Tests for ToolUseSFTConfig."""

    def test_defaults(self):
        config = ToolUseSFTConfig()
        assert config.max_seq_length == 8192
        assert config.learning_rate == 1e-4

    def test_from_yaml(self, yaml_file):
        data = {"model_name": "Qwen/Qwen3.5-9B", "max_seq_length": 4096}
        path = yaml_file(data, "tool_use.yaml")
        config = ToolUseSFTConfig.from_yaml(path)
        assert config.model_name == "Qwen/Qwen3.5-9B"
        assert config.max_seq_length == 4096
