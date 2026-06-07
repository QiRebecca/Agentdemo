from datetime import datetime, timezone

from scientific_agent_from_scratch.memory import MemoryStore
from scientific_agent_from_scratch.state import MemoryRecord


def test_memory_roundtrip(tmp_path):
    store = MemoryStore(tmp_path)
    record = MemoryRecord(
        memory_id="m1",
        kind="episodic",
        text="typed tool execution trace",
        tags=["tool", "trace"],
        created_at=datetime.now(timezone.utc).isoformat(),
        source_run_id="run-test",
    )
    store.write(record)
    results = store.search("tool execution", top_k=3)
    assert results
    assert results[0]["memory_id"] == "m1"
