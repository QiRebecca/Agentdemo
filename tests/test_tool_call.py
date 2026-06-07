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
