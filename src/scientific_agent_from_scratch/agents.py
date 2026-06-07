from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scientific_agent_from_scratch.state import AgentState, TaskNode, ToolCall


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


class BaseAgent:
    name = "BaseAgent"

    def run(self, task: TaskNode, state: AgentState, kernel: Any) -> dict[str, Any]:
        raise NotImplementedError


class OrchestratorAgent(BaseAgent):
    name = "OrchestratorAgent"

    def run(self, task: TaskNode, state: AgentState, kernel: Any) -> dict[str, Any]:
        summary = {"goal": state.goal, "tokens": state.goal.split()[:12]}
        state.working_memory["parsed_goal"] = summary
        kernel.trace.append("goal_parsed", self.name, task.task_id, "success", state.goal, "goal parsed")
        return summary


class ResearchAgent(BaseAgent):
    name = "ResearchAgent"

    def run(self, task: TaskNode, state: AgentState, kernel: Any) -> dict[str, Any]:
        if task.description == "retrieve_context":
            context = kernel.context_router.retrieve_all(state.goal, top_k=3)
            state.retrieved_context.update(context)
            write_json(Path(state.run_dir) / "retrieved_context.json", state.retrieved_context)
            kernel.trace.append("rag_retrieved", self.name, task.task_id, "success", state.goal, "multi-index context retrieved", str(Path(state.run_dir) / "retrieved_context.json"))
            return context
        if task.description == "retrieve_memory":
            memories = kernel.memory_store.search(state.goal, 3)
            state.retrieved_context["memories"] = memories
            write_json(Path(state.run_dir) / "retrieved_context.json", state.retrieved_context)
            kernel.trace.append("memory_retrieved", self.name, task.task_id, "success", state.goal, f"{len(memories)} memories retrieved")
            return {"memories": memories}
        if task.description == "write_memory":
            text = "The SAGE architecture demo completed a task graph run with context retrieval, skill selection, typed tool execution, report writing, and verification."
            call = ToolCall("write_memory", {"kind": "episodic", "text": text, "tags": ["architecture-demo", "trace"], "source_run_id": state.run_id}, task.task_id, self.name)
            result = kernel.tool_registry.call(call)
            state.tool_results.append(result.to_dict())
            event = {"task_id": task.task_id, "tool_result": result.to_dict()}
            path = Path(state.run_dir) / "memory_writes.jsonl"
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, sort_keys=True, default=str) + "\n")
            state.generated_artifacts.append(str(path))
            kernel.trace.append("memory_written", self.name, task.task_id, result.status, "episodic summary", "memory write recorded", str(path))
            return event
        raise ValueError(f"ResearchAgent cannot handle {task.description}")


class SkillManagerAgent(BaseAgent):
    name = "SkillManagerAgent"

    def run(self, task: TaskNode, state: AgentState, kernel: Any) -> dict[str, Any]:
        query = "context synthesis typed tool execution reproducible report memory update"
        selected = kernel.skill_registry.retrieve(query, top_k=10)
        selected_names = {skill["name"] for skill in selected}
        for required in task.required_skills:
            if required not in selected_names and required in kernel.skill_registry.skills:
                selected.append(kernel.skill_registry.skills[required].to_dict())
        composition = kernel.skill_registry.compose_skills(selected)
        payload = {"selected_skills": selected, "composition": composition}
        state.selected_skills = selected
        write_json(Path(state.run_dir) / "selected_skills.json", payload)
        kernel.trace.append("skill_selected", self.name, task.task_id, "success", query, ",".join(skill["name"] for skill in selected), str(Path(state.run_dir) / "selected_skills.json"))
        kernel.trace.append("skill_composed", self.name, task.task_id, "success", "selected skills", "composition graph created", str(Path(state.run_dir) / "selected_skills.json"), composition)
        return payload


class BuilderAgent(BaseAgent):
    name = "BuilderAgent"

    def run(self, task: TaskNode, state: AgentState, kernel: Any) -> dict[str, Any]:
        if task.description == "plan_tool_usage":
            plan = {"tool_name": "run_calculation", "arguments": {"expression": "2 + 2"}, "purpose": "demonstrate typed tool execution"}
            state.working_memory["tool_plan"] = plan
            return plan
        if task.description == "execute_tool_step":
            plan = state.working_memory.get("tool_plan", {"tool_name": "run_calculation", "arguments": {"expression": "2 + 2"}})
            call = ToolCall(plan["tool_name"], plan["arguments"], task.task_id, self.name)
            kernel.trace.append("tool_called", self.name, task.task_id, "started", call.tool_name, json.dumps(call.arguments, sort_keys=True))
            result = kernel.tool_registry.call(call)
            state.tool_results.append(result.to_dict())
            kernel.trace.append("tool_observed", self.name, task.task_id, result.status, call.tool_name, json.dumps(result.to_dict(), sort_keys=True), str(Path(state.run_dir) / "tool_calls.jsonl"))
            return {"tool_call": call.to_dict(), "tool_result": result.to_dict()}
        raise ValueError(f"BuilderAgent cannot handle {task.description}")


class ReporterAgent(BaseAgent):
    name = "ReporterAgent"

    def run(self, task: TaskNode, state: AgentState, kernel: Any) -> dict[str, Any]:
        report = self._render_report(state)
        path = Path(state.run_dir) / "report.md"
        result = kernel.tool_registry.call(ToolCall("write_file", {"path": str(path), "content": report}, task.task_id, self.name))
        state.tool_results.append(result.to_dict())
        state.generated_artifacts.append(str(path))
        kernel.trace.append("file_written", self.name, task.task_id, result.status, "report.md", "architecture demo report written", str(path))
        return {"report_path": str(path), "tool_result": result.to_dict()}

    def _render_report(self, state: AgentState) -> str:
        docs = state.retrieved_context.get("documents", [])
        skills = [skill["name"] for skill in state.selected_skills]
        handoffs = [event.get("to_agent") for event in state.handoff_history]
        return "\n".join(
            [
                "# SAGE Architecture Demo Report",
                "",
                "## Goal",
                state.goal,
                "",
                "## Components Exercised",
                "- Task-graph planning",
                "- Multi-index retrieval over documents, memory, skills, and tools",
                "- Typed tool execution",
                "- Skill loading and composition",
                "- Multi-agent handoff",
                "- Structured trace logging",
                "",
                "## Retrieved Context Summary",
                f"Retrieved {len(docs)} note records and {len(state.retrieved_context.get('memories', []))} memory records.",
                "",
                "## Selected Skills",
                ", ".join(skills) if skills else "No skills selected.",
                "",
                "## Tool Call Summary",
                f"Recorded {len(state.tool_results)} tool result entries during the run.",
                "",
                "## Handoffs",
                ", ".join(name for name in handoffs if name) if handoffs else "No handoffs recorded.",
                "",
                "## Memory Update",
                "An episodic memory summary is written after report generation.",
                "",
                "## Reproducibility Notes",
                "This report is generated from deterministic local code. It is an architecture demonstration, not a scientific result.",
                "",
            ]
        )


class VerifierAgent(BaseAgent):
    name = "VerifierAgent"

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

    def run(self, task: TaskNode, state: AgentState, kernel: Any) -> dict[str, Any]:
        verification_path = Path(state.run_dir) / "verification.json"
        write_json(verification_path, {"pass": False, "status": "pending"})
        call = ToolCall("verify_artifacts", {"run_dir": state.run_dir, "required_files": self.REQUIRED_FILES}, task.task_id, self.name)
        result = kernel.tool_registry.call(call)
        verification = result.output
        write_json(verification_path, verification)
        event_type = "verification_passed" if verification.get("pass") else "verification_failed"
        kernel.trace.append(event_type, self.name, task.task_id, result.status, "required artifacts", json.dumps(verification, sort_keys=True), str(verification_path))
        return verification
