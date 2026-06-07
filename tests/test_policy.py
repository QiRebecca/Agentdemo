from scientific_agent_from_scratch.policy import DeterministicPolicy, create_policy


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

    tool_plan = policy.plan_tool_call("run a safe tool", [{"name": "run_calculation"}])
    assert tool_plan["tool_name"] == "run_calculation"
