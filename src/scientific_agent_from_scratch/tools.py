from __future__ import annotations

import ast
import json
import operator
from pathlib import Path
from typing import Any, Callable

from scientific_agent_from_scratch.rag import retrieve
from scientific_agent_from_scratch.state import ToolCall, ToolResult, ToolSpec
from scientific_agent_from_scratch.verifier import verify_run_artifacts


class SafeArithmetic:
    OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def evaluate(self, expression: str) -> int | float:
        tree = ast.parse(expression, mode="eval")
        return self._eval(tree.body)

    def _eval(self, node: ast.AST) -> int | float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in self.OPS:
            return self.OPS[type(node.op)](self._eval(node.left), self._eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in self.OPS:
            return self.OPS[type(node.op)](self._eval(node.operand))
        raise ValueError("unsupported arithmetic expression")


class ToolRegistry:
    def __init__(
        self,
        run_dir: Path | None = None,
        document_records: list[dict[str, Any]] | None = None,
        memory_store: Any | None = None,
        skill_registry: Any | None = None,
    ):
        self.run_dir = Path(run_dir) if run_dir else None
        self.document_records = document_records or []
        self.memory_store = memory_store
        self.skill_registry = skill_registry
        self._tools: dict[str, tuple[ToolSpec, Callable[[dict[str, Any]], dict[str, Any]]]] = {}
        self.register_defaults()

    def register(self, spec: ToolSpec, func: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        self._tools[spec.name] = (spec, func)

    def list_tools(self) -> list[dict[str, Any]]:
        return [spec.to_dict() for spec, _ in self._tools.values()]

    def get_spec(self, name: str) -> ToolSpec:
        return self._tools[name][0]

    def retrieve(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        return retrieve(query, self.list_tools(), ["name", "description"], top_k)

    def call(self, call: ToolCall) -> ToolResult:
        if call.tool_name not in self._tools:
            return ToolResult(call.tool_name, "error", {}, {"type": "unknown_tool", "message": call.tool_name})
        spec, func = self._tools[call.tool_name]
        validation_error = self._validate_inputs(spec, call.arguments)
        if validation_error:
            result = ToolResult(call.tool_name, "error", {}, validation_error)
        else:
            try:
                result = ToolResult(call.tool_name, "success", func(call.arguments), None)
            except Exception as exc:  # noqa: BLE001 - tool errors are intentionally structured.
                result = ToolResult(call.tool_name, "error", {}, {"type": type(exc).__name__, "message": str(exc)})
        self._record_call(call, result)
        return result

    def _validate_inputs(self, spec: ToolSpec, arguments: dict[str, Any]) -> dict[str, Any] | None:
        for key, rule in spec.input_schema.items():
            required = True
            expected = None
            if isinstance(rule, dict):
                required = rule.get("required", True)
                expected = rule.get("type")
            else:
                expected = str(rule)
            if required and key not in arguments:
                return {"type": "validation_error", "message": f"missing required input: {key}"}
            if key in arguments and expected:
                py_type = {
                    "str": str,
                    "int": int,
                    "list": list,
                    "dict": dict,
                    "bool": bool,
                    "number": (int, float),
                }.get(expected)
                if py_type and not isinstance(arguments[key], py_type):
                    return {"type": "validation_error", "message": f"{key} must be {expected}"}
        return None

    def _record_call(self, call: ToolCall, result: ToolResult) -> None:
        if not self.run_dir:
            return
        path = self.run_dir / "tool_calls.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        event = {"call": call.to_dict(), "result": result.to_dict()}
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True, default=str) + "\n")

    def register_defaults(self) -> None:
        self.register(
            ToolSpec("search_docs", "Search local architecture notes by keyword.", {"query": "str", "top_k": "int"}, {"records": "list"}, "read", []),
            lambda args: {"records": retrieve(args["query"], self.document_records, ["title", "text", "path"], args["top_k"])},
        )
        self.register(
            ToolSpec("search_memory", "Search local episodic or semantic memory.", {"query": "str", "top_k": "int"}, {"records": "list"}, "read", []),
            lambda args: {"records": self.memory_store.search(args["query"], args["top_k"]) if self.memory_store else []},
        )
        self.register(
            ToolSpec(
                "write_memory",
                "Write a memory record to local JSONL memory.",
                {"kind": "str", "text": "str", "tags": "list", "source_run_id": {"type": "str", "required": False}},
                {"memory_id": "str", "path": "str"},
                "write",
                [],
            ),
            self._write_memory,
        )
        self.register(
            ToolSpec("list_skills", "List or search reusable local skills.", {"query": {"type": "str", "required": False}}, {"skills": "list"}, "read", []),
            lambda args: {"skills": self.skill_registry.retrieve(args.get("query", ""), 10) if args.get("query") and self.skill_registry else (self.skill_registry.list() if self.skill_registry else [])},
        )
        self.register(
            ToolSpec("run_calculation", "Safely evaluate simple arithmetic.", {"expression": "str"}, {"value": "number"}, "execute", [{"expression": "2 + 2"}]),
            lambda args: {"value": SafeArithmetic().evaluate(args["expression"])},
        )
        self.register(
            ToolSpec(
                "validate_skill_contracts",
                "Confirm selected skills reference tools registered in the ToolRegistry.",
                {"selected_skills": "list", "registered_tools": "list"},
                {"pass": "bool", "missing_tools": "list", "checked_skills": "list"},
                "read",
                [],
            ),
            self._validate_skill_contracts,
        )
        self.register(
            ToolSpec(
                "build_execution_manifest",
                "Build a compact reproducibility manifest from runtime state.",
                {
                    "run_id": "str",
                    "task_graph": "list",
                    "retrieved_context": "dict",
                    "selected_skills": "list",
                    "tool_results": "list",
                },
                {"manifest": "dict"},
                "write",
                [],
            ),
            self._build_execution_manifest,
        )
        self.register(
            ToolSpec("write_file", "Write text to a local file path.", {"path": "str", "content": "str"}, {"path": "str", "bytes_written": "int"}, "write", []),
            self._write_file,
        )
        self.register(
            ToolSpec("read_file", "Read a local text file.", {"path": "str"}, {"content": "str"}, "read", []),
            self._read_file,
        )
        self.register(
            ToolSpec("verify_artifacts", "Verify required run artifacts exist.", {"run_dir": "str", "required_files": "list"}, {"pass": "bool"}, "read", []),
            lambda args: verify_run_artifacts(Path(args["run_dir"]), args["required_files"]),
        )

    def _write_memory(self, args: dict[str, Any]) -> dict[str, Any]:
        if not self.memory_store:
            raise RuntimeError("memory store is not configured")
        record = self.memory_store.write_text(args["kind"], args["text"], args["tags"], args.get("source_run_id"))
        return {"memory_id": record.memory_id, "path": str(self.memory_store._path_for_kind(record.kind))}

    def _write_file(self, args: dict[str, Any]) -> dict[str, Any]:
        path = self._resolve_run_path(args["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(args["content"], encoding="utf-8")
        return {"path": str(path), "bytes_written": len(args["content"].encode("utf-8"))}

    def _read_file(self, args: dict[str, Any]) -> dict[str, Any]:
        path = self._resolve_run_path(args["path"])
        return {"content": path.read_text(encoding="utf-8")}

    def _validate_skill_contracts(self, args: dict[str, Any]) -> dict[str, Any]:
        registered = {tool["name"] for tool in args["registered_tools"]}
        missing: list[str] = []
        checked: list[str] = []
        for skill in args["selected_skills"]:
            checked.append(str(skill.get("name", "unknown")))
            for tool_name in skill.get("required_tools", []):
                if tool_name not in registered and tool_name not in missing:
                    missing.append(tool_name)
        return {"pass": not missing, "missing_tools": missing, "checked_skills": checked}

    def _build_execution_manifest(self, args: dict[str, Any]) -> dict[str, Any]:
        context = args["retrieved_context"]
        manifest = {
            "run_id": args["run_id"],
            "task_count": len(args["task_graph"]),
            "selected_skill_count": len(args["selected_skills"]),
            "retrieved_document_count": len(context.get("documents", [])),
            "retrieved_memory_count": len(context.get("memories", [])),
            "tool_result_count": len(args["tool_results"]),
            "artifact_summary": {
                "has_task_graph": bool(args["task_graph"]),
                "has_retrieved_context": bool(context),
                "has_selected_skills": bool(args["selected_skills"]),
            },
            "deterministic": True,
        }
        return {"manifest": manifest}

    def _resolve_run_path(self, path_value: str) -> Path:
        path = Path(path_value)
        if not self.run_dir:
            return path
        run_root = self.run_dir.resolve()
        resolved = path.resolve()
        if not path.is_absolute():
            try:
                resolved.relative_to(run_root)
            except ValueError:
                resolved = (self.run_dir / path).resolve()
        try:
            resolved.relative_to(run_root)
        except ValueError as exc:
            raise PermissionError(f"path is outside run directory: {path}") from exc
        return resolved
