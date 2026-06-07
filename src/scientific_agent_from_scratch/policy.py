from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import Any


class PolicyError(RuntimeError):
    """Raised when a model-backed policy cannot produce a valid decision."""


class AgentPolicy(ABC):
    name = "base"
    model: str | None = None

    @abstractmethod
    def parse_goal(self, goal: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def select_skills(
        self,
        goal: str,
        candidates: list[dict[str, Any]],
        required_skill_names: list[str],
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def plan_tool_call(
        self,
        goal: str,
        available_tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def draft_report(self, state_snapshot: dict[str, Any]) -> str:
        raise NotImplementedError

    @abstractmethod
    def summarize_memory(self, state_snapshot: dict[str, Any]) -> str:
        raise NotImplementedError

    def metadata(self) -> dict[str, Any]:
        return {"name": self.name, "model": self.model}


class DeterministicPolicy(AgentPolicy):
    name = "deterministic"
    model = None

    def parse_goal(self, goal: str) -> dict[str, Any]:
        return {
            "goal": goal,
            "tokens": goal.split()[:12],
            "summary": goal,
            "success_criteria": [
                "task graph is created",
                "context is retrieved",
                "typed architecture tools are executed",
                "report, memory, trace, and verification artifacts are written",
            ],
        }

    def select_skills(
        self,
        goal: str,
        candidates: list[dict[str, Any]],
        required_skill_names: list[str],
    ) -> dict[str, Any]:
        names = [skill["name"] for skill in candidates]
        for required in required_skill_names:
            if required not in names:
                names.append(required)
        return {
            "selected_names": names,
            "rationale": "Selected deterministic demo skills required by the task graph.",
        }

    def plan_tool_call(
        self,
        goal: str,
        available_tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "tool_name": "build_execution_manifest",
            "arguments": {},
            "purpose": "build a reproducibility manifest from the current agent run state",
        }

    def draft_report(self, state_snapshot: dict[str, Any]) -> str:
        goal = state_snapshot["goal"]
        docs = state_snapshot.get("retrieved_context", {}).get("documents", [])
        memories = state_snapshot.get("retrieved_context", {}).get("memories", [])
        skills = [skill["name"] for skill in state_snapshot.get("selected_skills", [])]
        handoffs = [event.get("to_agent") for event in state_snapshot.get("handoff_history", [])]
        tool_results = state_snapshot.get("tool_results", [])
        return "\n".join(
            [
                "# SAGE Agent Run Report",
                "",
                "## Goal",
                goal,
                "",
                "## Components Exercised",
                "- Task-graph planning",
                "- Multi-index retrieval over documents, memory, skills, and tools",
                "- Typed tool execution",
                "- Skill loading and composition",
                "- Specialist-agent handoff",
                "- Structured trace logging",
                "",
                "## Retrieved Context Summary",
                f"Retrieved {len(docs)} note records and {len(memories)} memory records.",
                "",
                "## Selected Skills",
                ", ".join(skills) if skills else "No skills selected.",
                "",
                "## Tool Call Summary",
                f"Recorded {len(tool_results)} tool result entries during the run.",
                "",
                "## Handoffs",
                ", ".join(name for name in handoffs if name) if handoffs else "No handoffs recorded.",
                "",
                "## Memory Update",
                "An episodic memory summary is written after report generation.",
                "",
                "## Reproducibility Notes",
                "This report is generated from local runtime state and records the artifacts needed to inspect the run.",
                "",
            ]
        )

    def summarize_memory(self, state_snapshot: dict[str, Any]) -> str:
        return (
            "The SAGE agent run completed a task graph workflow with context retrieval, "
            "skill selection, typed tool execution, report writing, memory writing, and verification."
        )


class OpenAIResponsesPolicy(AgentPolicy):
    name = "openai"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: int = 60,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise PolicyError("OPENAI_API_KEY is required for the OpenAI policy")
        self.model = model or os.environ.get("SAGE_OPENAI_MODEL", "gpt-4.1-mini")
        self.timeout = timeout

    def parse_goal(self, goal: str) -> dict[str, Any]:
        schema = {
            "summary": "one sentence",
            "constraints": ["constraint"],
            "success_criteria": ["criterion"],
            "task_hints": ["hint"],
        }
        return self._json_decision(
            "Parse the user goal for an agent runtime. Return compact JSON only.",
            {"goal": goal, "schema": schema},
            required_keys=["summary", "success_criteria"],
        )

    def select_skills(
        self,
        goal: str,
        candidates: list[dict[str, Any]],
        required_skill_names: list[str],
    ) -> dict[str, Any]:
        candidate_names = [skill["name"] for skill in candidates]
        decision = self._json_decision(
            (
                "Select reusable skills for an agent run. Return JSON only with "
                "selected_names and rationale. Choose only names from candidate_names."
            ),
            {
                "goal": goal,
                "candidate_names": candidate_names,
                "required_skill_names": required_skill_names,
                "candidates": candidates,
            },
            required_keys=["selected_names"],
        )
        selected = [name for name in decision.get("selected_names", []) if name in candidate_names]
        for required in required_skill_names:
            if required in candidate_names and required not in selected:
                selected.append(required)
        decision["selected_names"] = selected
        return decision

    def plan_tool_call(
        self,
        goal: str,
        available_tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        allowed_names = [tool["name"] for tool in available_tools]
        decision = self._json_decision(
            (
                "Plan the main safe typed tool step for this agent run. Return JSON only "
                "with tool_name, arguments, and purpose. Prefer build_execution_manifest when available."
            ),
            {
                "goal": goal,
                "available_tools": available_tools,
                "allowed_tool_names": allowed_names,
                "required_output_schema": {
                    "tool_name": "str",
                    "arguments": "dict",
                    "purpose": "str",
                },
            },
            required_keys=["tool_name", "arguments"],
        )
        if decision["tool_name"] not in allowed_names:
            raise PolicyError(f"model selected unavailable tool: {decision['tool_name']}")
        return decision

    def draft_report(self, state_snapshot: dict[str, Any]) -> str:
        report = self._text_decision(
            (
                "Write a concise Markdown agent run report from the provided runtime state. "
                "Keep the report focused on runtime state, artifacts, tool observations, and reproducibility. "
                "Include Goal, Components Exercised, Retrieved Context Summary, Selected Skills, "
                "Tool Call Summary, Handoffs, Memory Update, and Reproducibility Notes."
            ),
            state_snapshot,
            max_output_tokens=1200,
        )
        return report.strip() + "\n"

    def summarize_memory(self, state_snapshot: dict[str, Any]) -> str:
        text = self._text_decision(
            (
                "Write one short episodic memory sentence summarizing this completed agent run. "
                "Do not include private data, API keys, or unsupported external claims."
            ),
            state_snapshot,
            max_output_tokens=200,
        )
        return " ".join(text.strip().split())

    def _json_decision(
        self,
        instructions: str,
        payload: dict[str, Any],
        required_keys: list[str],
    ) -> dict[str, Any]:
        text = self._text_decision(
            instructions + " Return valid JSON with no Markdown fences.",
            payload,
            max_output_tokens=700,
        )
        data = _parse_json_object(text)
        missing = [key for key in required_keys if key not in data]
        if missing:
            raise PolicyError(f"model response missing required keys: {missing}")
        return data

    def _text_decision(
        self,
        instructions: str,
        payload: dict[str, Any],
        max_output_tokens: int,
    ) -> str:
        body = {
            "model": self.model,
            "instructions": instructions,
            "input": json.dumps(payload, indent=2, sort_keys=True, default=str),
            "max_output_tokens": max_output_tokens,
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "sage-agent-framework/0.1",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            message = _safe_error_message(exc)
            raise PolicyError(f"OpenAI Responses API request failed: HTTP {exc.code}: {message}") from exc
        except urllib.error.URLError as exc:
            raise PolicyError(f"OpenAI Responses API request failed: {exc.reason}") from exc

        text = _extract_response_text(data)
        if not text.strip():
            raise PolicyError("OpenAI Responses API returned no text output")
        return text


class OpenAIChatCompletionsPolicy(OpenAIResponsesPolicy):
    name = "openai-chat"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: int = 60,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise PolicyError("OPENAI_API_KEY is required for the OpenAI-compatible chat policy")
        self.model = model or os.environ.get("SAGE_OPENAI_MODEL", "gpt-5.4-mini")
        self.base_url = (base_url or os.environ.get("SAGE_OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.timeout = timeout

    def metadata(self) -> dict[str, Any]:
        return {"name": self.name, "model": self.model, "base_url": self.base_url}

    def _text_decision(
        self,
        instructions: str,
        payload: dict[str, Any],
        max_output_tokens: int,
    ) -> str:
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": json.dumps(payload, indent=2, sort_keys=True, default=str)},
            ],
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "sage-agent-framework/0.1",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            message = _safe_error_message(exc)
            raise PolicyError(f"Chat Completions request failed: HTTP {exc.code}: {message}") from exc
        except urllib.error.URLError as exc:
            raise PolicyError(f"Chat Completions request failed: {exc.reason}") from exc

        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise PolicyError("Chat Completions response did not contain message content") from exc
        if not str(text).strip():
            raise PolicyError("Chat Completions response returned no text output")
        return str(text)


def create_policy(
    backend: str = "deterministic",
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> AgentPolicy:
    if backend == "deterministic":
        return DeterministicPolicy()
    if backend == "openai":
        return OpenAIResponsesPolicy(api_key=api_key, model=model)
    if backend == "openai-chat":
        return OpenAIChatCompletionsPolicy(api_key=api_key, model=model, base_url=base_url)
    raise ValueError(f"unknown policy backend: {backend}")


def _extract_response_text(response: dict[str, Any]) -> str:
    if isinstance(response.get("output_text"), str):
        return response["output_text"]
    chunks: list[str] = []
    for item in response.get("output", []):
        for content in item.get("content", []):
            if isinstance(content.get("text"), str):
                chunks.append(content["text"])
    return "\n".join(chunks)


def _parse_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", stripped, re.DOTALL)
    if fenced:
        stripped = fenced.group(1).strip()
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, re.DOTALL)
        if not match:
            raise PolicyError("model response did not contain a JSON object")
        value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise PolicyError("model response JSON was not an object")
    return value


def _safe_error_message(exc: urllib.error.HTTPError) -> str:
    body = exc.read().decode("utf-8", errors="replace")
    body = re.sub(r"Incorrect API key provided:[^.\n]*\.", "Incorrect API key provided: REDACTED.", body)
    body = re.sub(r"sk-[^\s\"']+", "sk-REDACTED", body)
    body = re.sub(r"Bearer\s+[A-Za-z0-9._-]+", "Bearer REDACTED", body)
    return body[:500]
