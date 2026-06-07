from __future__ import annotations

from scientific_agent_from_scratch.state import TaskNode


class TaskGraphPlanner:
    def plan(self, goal: str) -> list[TaskNode]:
        graph = [
            TaskNode("T1", "parse_goal", [], "OrchestratorAgent", [], []),
            TaskNode("T2", "retrieve_context", ["T1"], "ResearchAgent", ["search_docs"], []),
            TaskNode("T3", "retrieve_memory", ["T1"], "ResearchAgent", ["search_memory"], []),
            TaskNode(
                "T4",
                "select_skills",
                ["T2", "T3"],
                "SkillManagerAgent",
                ["list_skills"],
                ["context_synthesis", "tool_execution", "report_writing", "memory_update"],
            ),
            TaskNode("T5", "plan_tool_usage", ["T4"], "BuilderAgent", [], []),
            TaskNode("T6", "execute_tool_step", ["T5"], "BuilderAgent", ["run_calculation"], []),
            TaskNode("T7", "write_report", ["T2", "T4", "T6"], "ReporterAgent", ["write_file"], ["report_writing"]),
            TaskNode("T8", "write_memory", ["T7"], "ResearchAgent", ["write_memory"], ["memory_update"]),
            TaskNode("T9", "verify_run", ["T8"], "VerifierAgent", ["verify_artifacts"], []),
        ]
        self.validate(graph)
        return graph

    def validate(self, graph: list[TaskNode]) -> None:
        ids = {node.task_id for node in graph}
        for node in graph:
            missing = [dep for dep in node.dependencies if dep not in ids]
            if missing:
                raise ValueError(f"{node.task_id} has missing dependencies: {missing}")
        self._validate_acyclic(graph)

    def _validate_acyclic(self, graph: list[TaskNode]) -> None:
        deps = {node.task_id: set(node.dependencies) for node in graph}
        temporary: set[str] = set()
        permanent: set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in permanent:
                return
            if node_id in temporary:
                raise ValueError("task graph contains a cycle")
            temporary.add(node_id)
            for dep in deps[node_id]:
                visit(dep)
            temporary.remove(node_id)
            permanent.add(node_id)

        for task_id in deps:
            visit(task_id)

    def dependency_order(self, graph: list[TaskNode]) -> list[TaskNode]:
        ordered: list[TaskNode] = []
        remaining = {node.task_id: node for node in graph}
        completed: set[str] = set()
        while remaining:
            ready = [node for node in remaining.values() if set(node.dependencies) <= completed]
            if not ready:
                raise ValueError("task graph cannot be ordered")
            ready.sort(key=lambda node: node.task_id)
            for node in ready:
                ordered.append(node)
                completed.add(node.task_id)
                remaining.pop(node.task_id)
        return ordered
