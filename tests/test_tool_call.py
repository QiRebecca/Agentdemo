from scientific_agent_from_scratch.state import ToolCall
from scientific_agent_from_scratch.tools import ToolRegistry


def test_tool_call_success_and_error():
    registry = ToolRegistry()
    result = registry.call(ToolCall("run_calculation", {"expression": "2 + 2"}, "T6", "test"))
    assert result.status == "success"
    assert result.output["value"] == 4

    missing = registry.call(ToolCall("run_calculation", {}, "T6", "test"))
    assert missing.status == "error"
    assert missing.error["type"] == "validation_error"

    invalid = registry.call(ToolCall("run_calculation", {"expression": "2 + bad"}, "T6", "test"))
    assert invalid.status == "error"
    assert invalid.error is not None


def test_file_tools_are_limited_to_run_dir(tmp_path):
    registry = ToolRegistry(run_dir=tmp_path)
    inside = tmp_path / "report.md"

    written = registry.call(ToolCall("write_file", {"path": str(inside), "content": "ok"}, "T7", "test"))
    assert written.status == "success"

    outside = tmp_path.parent / "outside.md"
    blocked = registry.call(ToolCall("write_file", {"path": str(outside), "content": "no"}, "T7", "test"))
    assert blocked.status == "error"
    assert blocked.error is not None


def test_architecture_tools_validate_contracts_and_manifest():
    registry = ToolRegistry()
    skills = [{"name": "report_writing", "required_tools": ["write_file"]}]
    tools = registry.list_tools()

    contracts = registry.call(
        ToolCall("validate_skill_contracts", {"selected_skills": skills, "registered_tools": tools}, "T6", "test")
    )
    assert contracts.status == "success"
    assert contracts.output["pass"] is True
    assert contracts.output["checked_skills"] == ["report_writing"]

    manifest = registry.call(
        ToolCall(
            "build_execution_manifest",
            {
                "run_id": "run_test",
                "task_graph": [{"task_id": "T1"}],
                "retrieved_context": {"documents": [{"id": "doc"}], "memories": []},
                "selected_skills": skills,
                "tool_results": [contracts.to_dict()],
            },
            "T6",
            "test",
        )
    )
    assert manifest.status == "success"
    assert manifest.output["manifest"]["run_id"] == "run_test"
    assert manifest.output["manifest"]["retrieved_document_count"] == 1
