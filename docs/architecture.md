# Architecture

SAGE is a compact agent framework with pluggable policy backends. The central object is `AgentKernel`, which initializes state, builds a task graph, routes context retrieval, selects skills, dispatches specialist agents, records handoffs, calls typed tools, writes local artifacts, and verifies the run.

The runtime is intentionally small so the control flow is inspectable. A reviewer can follow a run from `run_config.json` to `task_graph.json`, then through retrieval, skill selection, tool calls, handoffs, memory writes, and `trace.jsonl`.

## Component Map

| Component      | File                | What it demonstrates                       |
| -------------- | ------------------- | ------------------------------------------ |
| Agent kernel   | `kernel.py`         | Runtime state, task execution, lifecycle      |
| Policy layer   | `policy.py`         | Deterministic and OpenAI-backed decisions     |
| Task graph     | `task_graph.py`     | Long-horizon task decomposition               |
| Context router | `context_router.py` | Retrieval over docs, memory, tools, skills    |
| Tool registry  | `tools.py`          | Typed tool use, path sandboxing, errors       |
| Skill registry | `skills.py`         | Procedural memory and skill composition       |
| Handoffs       | `handoff.py`        | Specialist-agent state transfer               |
| Trace logger   | `trace.py`          | Inspectable execution trace                   |
| Verifier       | `verifier.py`       | Artifact completeness checks                  |

## Policy Backends

SAGE separates runtime mechanics from policy decisions.

- `DeterministicPolicy` runs without external APIs and is used by the smoke tests.
- `OpenAIResponsesPolicy` uses the OpenAI Responses API for goal parsing, skill selection, typed tool planning, report drafting, and memory summarization.
- `OpenAIChatCompletionsPolicy` supports OpenAI-compatible `/chat/completions` providers through a configurable base URL.

Both policies feed the same kernel, tools, memory store, skill registry, handoff logger, and trace logger. This makes the model-backed path real without coupling the framework to one provider-specific orchestration library.

## Multi-Index Retrieval

RAG in SAGE is not only document retrieval. It is a routing layer over documents, memories, tools, and skills. This makes retrieval part of the agent control plane: the runtime can retrieve factual context from notes, prior run summaries from memory, callable capabilities from the tool registry, and reusable procedures from the skill registry.

The implementation uses deterministic keyword retrieval rather than embeddings or external services. This keeps the public demo reproducible and easy to audit.

## Skills As Procedural Memory

Skills are treated as procedural memory because they encode reusable task procedures rather than factual content. Each skill has a `manifest.json` for machine-readable metadata and a `SKILL.md` for human-readable procedure details. The registry can retrieve relevant skills and compose them into a simple ordered execution plan.

## Traces As First-Class Artifacts

Traces are first-class artifacts. A run is considered inspectable only if task creation, retrieval, skill selection, handoff, tool call, observation, memory write, and verification are recorded. `trace.jsonl` is designed to show what happened without requiring hidden prompts, private state, or external service logs.

## Agent Roles And Outputs

- `OrchestratorAgent`: parses the goal and stores a compact working-memory representation.
- `ResearchAgent`: retrieves context and memory, writes `retrieved_context.json`, and records episodic memory in `memory_writes.jsonl`.
- `SkillManagerAgent`: retrieves and composes skills, then writes `selected_skills.json`.
- `BuilderAgent`: plans and executes a typed tool call, recording observations in `tool_calls.jsonl`.
- `ReporterAgent`: writes `report.md`, a short architecture demo report.
- `VerifierAgent`: checks required run artifacts and writes `verification.json`.
