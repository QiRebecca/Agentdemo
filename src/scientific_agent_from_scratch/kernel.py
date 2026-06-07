from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from scientific_agent_from_scratch.agents import (
    BuilderAgent,
    OrchestratorAgent,
    ReporterAgent,
    ResearchAgent,
    SkillManagerAgent,
    VerifierAgent,
    write_json,
)
from scientific_agent_from_scratch.context_router import ContextRouter, load_note_records
from scientific_agent_from_scratch.handoff import record_handoff
from scientific_agent_from_scratch.memory import MemoryStore
from scientific_agent_from_scratch.skills import SkillRegistry
from scientific_agent_from_scratch.state import AgentState, TaskNode
from scientific_agent_from_scratch.task_graph import TaskGraphPlanner
from scientific_agent_from_scratch.tools import ToolRegistry
from scientific_agent_from_scratch.trace import TraceLogger


class AgentKernel:
    def __init__(self, base_dir: Path | str | None = None, asset_root: Path | str | None = None):
        self.project_root = Path(asset_root) if asset_root else Path(__file__).resolve().parents[2]
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.notes_root = self.project_root / "notes"
        self.skills_root = self.project_root / "skills"
        self.memory_store = MemoryStore(self.base_dir / ".sage_memory")
        self.skill_registry = SkillRegistry(self.skills_root)
        self.documents = load_note_records(self.notes_root)
        self.tool_registry = ToolRegistry(document_records=self.documents, memory_store=self.memory_store, skill_registry=self.skill_registry)
        self.context_router = ContextRouter(self.notes_root, self.memory_store, self.skill_registry, self.tool_registry)
        self.planner = TaskGraphPlanner()
        self.trace: TraceLogger = TraceLogger(self.base_dir / ".sage_runs" / "_boot" / "trace.jsonl")
        self.agents = {
            "OrchestratorAgent": OrchestratorAgent(),
            "ResearchAgent": ResearchAgent(),
            "SkillManagerAgent": SkillManagerAgent(),
            "BuilderAgent": BuilderAgent(),
            "ReporterAgent": ReporterAgent(),
            "VerifierAgent": VerifierAgent(),
        }

    def create_state(self, goal: str, run_dir: Path | str) -> AgentState:
        run_path = Path(run_dir)
        return AgentState(run_id=run_path.name or str(uuid4()), goal=goal, run_dir=str(run_path))

    def run(self, goal: str, run_dir: Path | None = None) -> AgentState:
        run_path = Path(run_dir) if run_dir else self._next_run_dir()
        run_path.mkdir(parents=True, exist_ok=True)
        self.trace = TraceLogger(run_path / "trace.jsonl")
        self.tool_registry = ToolRegistry(run_path, self.documents, self.memory_store, self.skill_registry)
        self.context_router = ContextRouter(self.notes_root, self.memory_store, self.skill_registry, self.tool_registry)
        state = self.create_state(goal, run_path)
        state.status = "running"
        self.trace.append("run_started", "AgentKernel", None, "started", goal, state.run_id, str(run_path / "trace.jsonl"))

        try:
            write_json(run_path / "run_config.json", {"run_id": state.run_id, "goal": goal, "runtime": "SAGE deterministic architecture demo"})
            graph = self.planner.plan(goal)
            state.task_graph = graph
            write_json(run_path / "task_graph.json", [node.to_dict() for node in graph])
            self.trace.append("task_graph_created", "TaskGraphPlanner", "T0", "success", goal, f"{len(graph)} tasks", str(run_path / "task_graph.json"))
            for task in self.planner.dependency_order(graph):
                self._execute_task(task, state)
                if state.status == "failed":
                    break
            if state.status != "failed":
                state.status = "completed"
                self.trace.append("run_finished", "AgentKernel", None, "completed", state.goal, "run completed")
        except Exception as exc:  # noqa: BLE001 - kernel records failure before returning.
            state.status = "failed"
            self.trace.append("run_finished", "AgentKernel", state.active_task_id, "failed", state.goal, str(exc), metadata={"error_type": type(exc).__name__})
            try:
                VerifierAgent().run(TaskNode("T9", "verify_run", [], "VerifierAgent", ["verify_artifacts"], []), state, self)
            except Exception:
                pass
        return state

    def _execute_task(self, task: TaskNode, state: AgentState) -> None:
        state.active_task_id = task.task_id
        task.status = "running"
        handoff = record_handoff(Path(state.run_dir), self.trace, "AgentKernel", task.assigned_agent, task.task_id, task.description)
        state.handoff_history.append(handoff)
        agent = self.agents[task.assigned_agent]
        try:
            output = agent.run(task, state, self)
            task.outputs = output
            task.status = "completed"
        except Exception as exc:  # noqa: BLE001
            task.status = "failed"
            task.failure_reason = str(exc)
            state.status = "failed"
            self.trace.append("run_finished", task.assigned_agent, task.task_id, "failed", task.description, str(exc), metadata={"error_type": type(exc).__name__})
        finally:
            write_json(Path(state.run_dir) / "task_graph.json", [node.to_dict() for node in state.task_graph])

    def _next_run_dir(self) -> Path:
        root = self.base_dir / ".sage_runs"
        root.mkdir(parents=True, exist_ok=True)
        index = 1
        while True:
            candidate = root / f"run_{index:03d}"
            if not candidate.exists():
                return candidate
            index += 1
