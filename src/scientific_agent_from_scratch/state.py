from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any


def to_dict(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [to_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: to_dict(item) for key, item in value.items()}
    return value


@dataclass
class TaskNode:
    task_id: str
    description: str
    dependencies: list[str]
    assigned_agent: str
    required_tools: list[str]
    required_skills: list[str]
    status: str = "pending"
    outputs: dict[str, Any] = field(default_factory=dict)
    failure_reason: str | None = None
    retry_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentState:
    run_id: str
    goal: str
    run_dir: str
    task_graph: list[TaskNode] = field(default_factory=list)
    active_task_id: str | None = None
    retrieved_context: dict[str, Any] = field(default_factory=dict)
    selected_skills: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    working_memory: dict[str, Any] = field(default_factory=dict)
    handoff_history: list[dict[str, Any]] = field(default_factory=list)
    generated_artifacts: list[str] = field(default_factory=list)
    status: str = "initialized"

    def to_dict(self) -> dict[str, Any]:
        return to_dict(self)


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    permission: str
    examples: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ToolCall:
    tool_name: str
    arguments: dict[str, Any]
    task_id: str
    caller: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ToolResult:
    tool_name: str
    status: str
    output: dict[str, Any]
    error: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SkillSpec:
    name: str
    description: str
    when_to_use: str
    required_tools: list[str]
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    validation: list[str]
    path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryRecord:
    memory_id: str
    kind: str
    text: str
    tags: list[str]
    created_at: str
    source_run_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HandoffEvent:
    event_id: str
    from_agent: str
    to_agent: str
    task_id: str
    expected_output: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
