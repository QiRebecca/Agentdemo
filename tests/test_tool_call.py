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
