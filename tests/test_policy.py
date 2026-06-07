import pytest

from scientific_agent_from_scratch.policy import (
    DeterministicPolicy,
    OpenAIChatCompletionsPolicy,
    OpenAIResponsesPolicy,
    PolicyError,
    create_policy,
)


def test_policy_factory_and_deterministic_decisions():
    policy = create_policy("deterministic")
    assert isinstance(policy, DeterministicPolicy)

    parsed = policy.parse_goal("run a tool and write a report")
    assert parsed["summary"]

    skills = [
        {"name": "tool_execution", "description": "execute tools", "when_to_use": "tool call"},
        {"name": "report_writing", "description": "write report", "when_to_use": "report"},
    ]
    selected = policy.select_skills("write report", skills, ["report_writing"])
    assert "report_writing" in selected["selected_names"]

    tool_plan = policy.plan_tool_call("run a safe tool", [{"name": "build_execution_manifest"}])
    assert tool_plan["tool_name"] == "build_execution_manifest"


def test_openai_chat_policy_factory_without_network():
    policy = create_policy(
        "openai-chat",
        model="example-model",
        api_key="test-key",
        base_url="https://example.test/v1",
    )
    assert isinstance(policy, OpenAIChatCompletionsPolicy)
    assert policy.metadata()["base_url"] == "https://example.test/v1"


def test_openai_responses_policy_factory_without_network():
    policy = create_policy("openai", model="example-model", api_key="test-key")
    assert isinstance(policy, OpenAIResponsesPolicy)
    assert policy.metadata()["model"] == "example-model"


def test_model_backed_policy_requires_model_without_network(monkeypatch):
    monkeypatch.delenv("SAGE_OPENAI_MODEL", raising=False)
    with pytest.raises(PolicyError, match="model name"):
        create_policy("openai-chat", api_key="test-key")


def test_model_backed_policy_uses_environment_model_without_network(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("SAGE_OPENAI_MODEL", "example-model")
    policy = create_policy("openai-chat", base_url="https://example.test/v1")
    assert policy.metadata()["model"] == "example-model"
