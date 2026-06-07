# SAGE: Scientific Agent Graph Engine

SAGE is a small, from-scratch agent framework for running inspectable long-horizon LLM-agent workflows: task-graph planning, multi-index retrieval, local memory, typed tool execution, reusable skills, specialist-agent handoff, structured tracing, runtime verification, and pluggable policy backends.

This repository is architecture-focused but runnable. The default deterministic policy runs locally without API keys, while the optional OpenAI policy uses the same runtime interfaces to make real model-backed planning, skill-selection, tool-planning, report-writing, and memory-summary decisions. SAGE is not a domain-specific scientific discovery project, not a benchmark-result repository, and not a wrapper around an external agent framework.

## What This Demonstrates

- Agent kernel from scratch: explicit state management, task execution, and run lifecycle.
- Task-graph planning: a natural-language goal is converted into an executable DAG.
- Multi-index retrieval: context is retrieved from documents, memory, tools, and skills.
- Hierarchical memory: working memory in `AgentState`, episodic memory in JSONL, and procedural memory as reusable skills.
- Typed tool use: tools have schemas, validation, normalized observations, and JSONL call traces.
- Skill loading and composition: skills are loaded from `manifest.json` + `SKILL.md`, retrieved by relevance, and composed into an execution plan.
- Specialist-agent handoff: Research, Skill Manager, Builder, Reporter, and Verifier agents exchange explicit state slices.
- Trace-first execution: every important runtime event is written to `trace.jsonl`.
- Pluggable policy backends: deterministic local policy by default, with optional OpenAI Responses API and OpenAI-compatible Chat Completions policies.
- Smoke-tested demo: the local architecture demo is covered by pytest smoke tests.

## What This Is Not

- Not a LangChain, LangGraph, AutoGen, CrewAI, or OpenAI Agents SDK wrapper.
- Not a chatbot demo.
- Not a biology-specific project.
- Not an auditing or benchmark-results repository.
- Not dependent on external APIs for the default deterministic run.
- Not allowed to store API keys or private data in the repository.

## Quickstart

```bash
python -m pip install -e ".[dev]"
python examples/run_agent.py
python -m pytest -q
```

If `python` is not Python 3.10 or newer on your system, use an explicit interpreter:

```bash
python3.10 -m pip install -e ".[dev]"
python3.10 examples/run_agent.py
python3.10 -m pytest -q
```

To run the OpenAI Responses API policy, export a key in your shell and choose the OpenAI policy:

```bash
export OPENAI_API_KEY="..."
python examples/run_agent.py --policy openai --model gpt-4.1-mini
```

To run an OpenAI-compatible Chat Completions provider, set the provider base URL:

```bash
export OPENAI_API_KEY="..."
python examples/run_agent.py \
  --policy openai-chat \
  --base-url https://api.example.com/v1 \
  --model provider-model-name
```

The key is read from the process environment. It should not be written to `.env` or committed.

## Expected Run Output

```text
SAGE agent run
Policy: deterministic
Status: completed
Trace: .sage_runs/run_001/trace.jsonl
Report: .sage_runs/run_001/report.md
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
   ^
   |
Policy Backend
   |-- DeterministicPolicy
   |-- OpenAIResponsesPolicy
   |-- OpenAIChatCompletionsPolicy
   |
   v
Trace + Local Run Artifacts
```

The key design choice is that retrieval is part of the agent control plane: SAGE retrieves not only documents, but also relevant memories, tools, and reusable skills.

## Why Deterministic By Default?

The default policy is deterministic so the runtime can be inspected and tested without external APIs, API keys, or nondeterministic model outputs. This keeps the core framework reproducible: state, task graph, retrieval, memory, tools, skills, handoffs, and traces can all be tested independently.

Model-backed policies are attached at the policy layer and reuse the same runtime components. This separation keeps model decisions replaceable while preserving tool validation, memory writes, handoff logging, and trace verification.

## Where An LLM Backend Would Attach

Runtime mechanics are separated from policy decisions. `DeterministicPolicy` is used for local tests and reproducibility. `OpenAIResponsesPolicy` uses the OpenAI Responses API, while `OpenAIChatCompletionsPolicy` supports OpenAI-compatible `/chat/completions` providers. Both model-backed policies can perform goal parsing, skill selection, typed tool planning, report drafting, and memory summarization.

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
  policy.py          # deterministic and OpenAI-backed policy backends
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
2. Run `python examples/run_agent.py`.
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
- No external APIs required for deterministic runs
- Optional model-backed policies through the OpenAI Responses API or compatible Chat Completions providers
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
- Model-backed policies require a valid `OPENAI_API_KEY`.
- The project is intended as a compact inspectable framework, not a full production platform.
