# SAGE: Scientific Agent Graph Engine

SAGE is a small, from-scratch agent runtime for demonstrating the core architecture of long-horizon LLM agents: task-graph planning, multi-index retrieval, local memory, typed tool execution, reusable skills, specialist-agent handoff, structured tracing, and runtime verification.

This repository is intentionally architecture-focused. It is not a domain-specific scientific discovery project, not a benchmark-result repository, and not a wrapper around an external agent framework. The default demo is deterministic and runs locally without API keys, so the runtime can be inspected, tested, and reproduced quickly.

## What This Demonstrates

- Agent kernel from scratch: explicit state management, task execution, and run lifecycle.
- Task-graph planning: a natural-language goal is converted into an executable DAG.
- Multi-index retrieval: context is retrieved from documents, memory, tools, and skills.
- Hierarchical memory: working memory in `AgentState`, episodic memory in JSONL, and procedural memory as reusable skills.
- Typed tool use: tools have schemas, validation, normalized observations, and JSONL call traces.
- Skill loading and composition: skills are loaded from `manifest.json` + `SKILL.md`, retrieved by relevance, and composed into an execution plan.
- Specialist-agent handoff: Research, Skill Manager, Builder, Reporter, and Verifier agents exchange explicit state slices.
- Trace-first execution: every important runtime event is written to `trace.jsonl`.
- Smoke-tested demo: the local architecture demo is covered by pytest smoke tests.

## What This Is Not

- Not a LangChain, LangGraph, AutoGen, CrewAI, or OpenAI Agents SDK wrapper.
- Not a chatbot demo.
- Not a biology-specific project.
- Not an auditing or benchmark-results repository.
- Not dependent on external APIs or private data.

## Quickstart

```bash
python -m pip install -e ".[dev]"
python examples/run_architecture_demo.py
python -m pytest -q
```

If `python` is not Python 3.10 or newer on your system, use an explicit interpreter:

```bash
python3.10 -m pip install -e ".[dev]"
python3.10 examples/run_architecture_demo.py
python3.10 -m pytest -q
```

## Expected Demo Output

```text
SAGE architecture demo

[1/9] Parsed goal
[2/9] Built task graph
[3/9] Retrieved context
[4/9] Retrieved memory
[5/9] Selected skills
[6/9] Executed typed tool call
[7/9] Wrote report
[8/9] Wrote memory
[9/9] Verified run

Run completed.
Verification: passed
```

## Generated Local Artifacts

Running the demo locally creates an ignored run directory:

```text
.sage_runs/run_001/
  run_config.json
  task_graph.json
  retrieved_context.json
  selected_skills.json
  tool_calls.jsonl
  handoffs.jsonl
  memory_writes.jsonl
  trace.jsonl
  report.md
  verification.json
```

These files are not committed to the repository. They are regenerated locally so reviewers can inspect the execution trace themselves.

## Architecture

```text
User Goal
   |
   v
TaskGraphPlanner
   |
   v
ContextRouter
   |-- Document RAG
   |-- Memory RAG
   |-- Skill RAG
   |-- Tool RAG
   |
   v
AgentKernel / Orchestrator
   |-- ResearchAgent
   |-- SkillManagerAgent
   |-- BuilderAgent
   |-- ReporterAgent
   |-- VerifierAgent
   |
   v
ToolRegistry + SkillRegistry + MemoryStore
   |
   v
Trace + Local Run Artifacts
```

The key design choice is that retrieval is part of the agent control plane: SAGE retrieves not only documents, but also relevant memories, tools, and reusable skills.

## Why Deterministic By Default?

The public demo uses deterministic policies so the runtime can be inspected and tested without external APIs, API keys, or nondeterministic model outputs. The goal of this repository is to expose the agent architecture: state, task graph, retrieval, memory, tools, skills, handoffs, and traces.

An LLM backend can be attached later at the policy layer, but the runtime components are intentionally implemented and tested independently.

## Where An LLM Backend Would Attach

The deterministic demo separates runtime mechanics from policy decisions. In a model-backed extension, the policy layer could replace deterministic choices for task refinement, tool selection, and report drafting, while reusing the same state, tool, memory, skill, handoff, and trace infrastructure.

## Code Map

```text
src/scientific_agent_from_scratch/
  kernel.py          # runtime core and task execution loop
  state.py           # AgentState, TaskNode, ToolSpec, SkillSpec, MemoryRecord
  task_graph.py      # deterministic DAG planner for the architecture demo
  context_router.py  # multi-index retrieval over docs, memory, tools, skills
  rag.py             # deterministic keyword retrieval
  memory.py          # JSONL episodic memory store
  tools.py           # typed tool registry and safe tool execution
  skills.py          # skill loading, retrieval, and composition
  agents.py          # specialist agents
  handoff.py         # structured handoff logging
  trace.py           # JSONL trace logger
  verifier.py        # artifact verification
```

## Smoke Tests

1. Kernel boot: the runtime initializes with tools and skills.
2. RAG router: document and skill retrieval return expected matches.
3. Memory roundtrip: episodic memory can be written and retrieved.
4. Tool call: typed tool execution validates input and returns structured output.
5. Skill activation: relevant skills can be retrieved and composed.
6. End-to-end demo: the architecture demo generates all required artifacts and a passing verification report.

## Reviewer Path

For a quick inspection:

1. Read the architecture diagram above.
2. Run `python examples/run_architecture_demo.py`.
3. Open `.sage_runs/run_001/trace.jsonl` to inspect execution events.
4. Open `.sage_runs/run_001/task_graph.json` to inspect the task DAG.
5. Run `python -m pytest -q` to verify the smoke tests.

## Example Trace Event

```json
{
  "event_type": "tool_called",
  "actor": "BuilderAgent",
  "task_id": "T6",
  "status": "started",
  "input_summary": "run_calculation(expression='2 + 2')"
}
```

## Design Principles

- Deterministic by default
- No external APIs
- Explicit state transitions
- Typed tools
- Skills as procedural memory
- Trace-first execution
- Generated artifacts kept out of git
- Smoke-tested local demo

## Limitations

- The public demo uses toy notes only.
- The demo does not claim scientific discoveries or benchmark results.
- Retrieval is keyword-based for inspectability.
- The default runtime does not call an LLM backend.
- The project is intended as an architecture demonstration, not a production agent framework.
