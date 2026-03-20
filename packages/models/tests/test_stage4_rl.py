"""Tests for Stage 4 Progressive RL reward function and config."""

from rare_archive_models.training.stage4_rl import (
    RLConfig,
    compute_reward,
)


DEFAULT_WEIGHTS = {
    "diagnostic_accuracy": 1.0,
    "reasoning_quality": 0.3,
    "tool_usage": 0.2,
    "safety": 0.5,
}


class TestComputeReward:
    """Tests for compute_reward()."""

    def test_correct_diagnosis_gives_accuracy_score(self):
        reward = compute_reward(
            "The diagnosis is Duchenne muscular dystrophy based on evidence.",
            "duchenne muscular dystrophy",
            DEFAULT_WEIGHTS,
            phase="reasoner",
        )
        # accuracy=2.0*1.0 + reasoning ("based on", "evidence") = 0.3 = 2.3
        assert reward >= 2.0

    def test_reasoning_keywords_boost_score(self):
        response_with = "Because the symptoms suggest this, considering differential diagnosis."
        response_without = "The answer is X."
        reward_with = compute_reward(response_with, "nonexistent", DEFAULT_WEIGHTS)
        reward_without = compute_reward(response_without, "nonexistent", DEFAULT_WEIGHTS)
        assert reward_with > reward_without

    def test_tool_usage_counted_in_retriever_phase(self):
        response = "Using tool_calls and function to retrieve data."
        reward_retriever = compute_reward(response, "nonexistent", DEFAULT_WEIGHTS, phase="retriever")
        reward_reasoner = compute_reward(response, "nonexistent", DEFAULT_WEIGHTS, phase="reasoner")
        assert reward_retriever > reward_reasoner

    def test_safety_penalty(self):
        safe = "Consider seeing a specialist for evaluation."
        dangerous = "Stop taking medication immediately."
        reward_safe = compute_reward(safe, "nonexistent", DEFAULT_WEIGHTS)
        reward_dangerous = compute_reward(dangerous, "nonexistent", DEFAULT_WEIGHTS)
        assert reward_safe > reward_dangerous
        assert reward_dangerous < 0

    def test_combined_weighted_score(self):
        response = "Based on evidence, the diagnosis is target disease"
        reward = compute_reward(response, "target disease", DEFAULT_WEIGHTS)
        # accuracy: 2.0*1.0=2.0, reasoning: 1.0*0.3=0.3, no tool (reasoner), no penalty
        assert abs(reward - 2.3) < 0.01

    def test_phase_specific_scoring(self):
        response = "Using function calls to investigate."
        reward_collab = compute_reward(response, "x", DEFAULT_WEIGHTS, phase="collaboration")
        reward_reason = compute_reward(response, "x", DEFAULT_WEIGHTS, phase="reasoner")
        # Collaboration includes tool_usage score, reasoner does not
        assert reward_collab > reward_reason


class TestRLConfig:
    """Tests for RLConfig dataclass."""

    def test_defaults(self):
        config = RLConfig()
        assert config.method == "grpo"
        assert config.phase == "reasoner"
        assert config.reward_weights["diagnostic_accuracy"] == 1.0
        assert config.reward_weights["safety"] == 0.5

    def test_from_yaml(self, yaml_file):
        data = {"phase": "retriever", "learning_rate": 5e-6}
        path = yaml_file(data, "rl.yaml")
        config = RLConfig.from_yaml(path)
        assert config.phase == "retriever"
        assert config.learning_rate == 5e-6
