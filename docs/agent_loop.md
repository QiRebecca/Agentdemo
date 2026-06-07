# Agent Loop

SAGE uses a deterministic loop:

```text
observe
  -> parse goal
  -> build task graph
  -> retrieve context
  -> select skills
  -> handoff
  -> act with tool
  -> observe tool result
  -> write report
  -> write memory
  -> verify
  -> finish
```

Each step updates explicit runtime state or writes an inspectable artifact. With `DeterministicPolicy`, the loop is local and reproducible. With `OpenAIResponsesPolicy`, policy decisions are model-backed while the same tool validation, memory write, handoff, trace, and verification infrastructure remains in control.

## Trace Example

```json
{
  "event_type": "tool_called",
  "actor": "BuilderAgent",
  "task_id": "T6",
  "status": "started",
  "input_summary": "run_calculation(expression='2 + 2')"
}
```

The trace is intentionally compact: it records event type, actor, task, status, summaries, artifact paths, and metadata.
