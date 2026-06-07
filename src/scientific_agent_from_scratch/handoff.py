from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from scientific_agent_from_scratch.state import HandoffEvent
from scientific_agent_from_scratch.trace import TraceLogger


def record_handoff(
    run_dir: Path,
    trace: TraceLogger,
    from_agent: str,
    to_agent: str,
    task_id: str,
    expected_output: str,
    status: str = "accepted",
) -> dict:
    event = HandoffEvent(str(uuid4()), from_agent, to_agent, task_id, expected_output, status).to_dict()
    event["timestamp"] = datetime.now(timezone.utc).isoformat()
    path = run_dir / "handoffs.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    trace.append("agent_handoff", from_agent, task_id, status, to_agent, expected_output, str(path), {"to_agent": to_agent})
    return event
