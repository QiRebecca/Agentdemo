import json
from pathlib import Path

from scientific_agent_from_scratch.kernel import AgentKernel


REQUIRED_FILES = [
    "run_config.json",
    "task_graph.json",
    "retrieved_context.json",
    "selected_skills.json",
    "tool_calls.jsonl",
    "handoffs.jsonl",
    "memory_writes.jsonl",
    "trace.jsonl",
    "report.md",
    "verification.json",
]


def test_architecture_demo(tmp_path):
    run_dir = tmp_path / "run"
    state = AgentKernel(base_dir=tmp_path).run("architecture demo goal", run_dir=run_dir)
    assert state.status == "completed"
    for name in REQUIRED_FILES:
        assert (run_dir / name).exists(), name
    verification = json.loads((run_dir / "verification.json").read_text(encoding="utf-8"))
    assert verification["pass"] is True
    run_config = json.loads((run_dir / "run_config.json").read_text(encoding="utf-8"))
    assert run_config["policy"]["name"] == "deterministic"
    trace_events = [
        json.loads(line)["event_type"]
        for line in (run_dir / "trace.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    for event_type in [
        "task_graph_created",
        "rag_retrieved",
        "skill_selected",
        "agent_handoff",
        "tool_called",
        "tool_observed",
        "memory_written",
        "verification_passed",
    ]:
        assert event_type in trace_events
