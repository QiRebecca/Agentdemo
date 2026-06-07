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

Each step updates explicit runtime state or writes an inspectable artifact. The loop is deterministic in the public demo so reviewers can inspect state transitions without depending on hidden model calls or external services.

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
