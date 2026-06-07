from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from scientific_agent_from_scratch.rag import retrieve
from scientific_agent_from_scratch.state import MemoryRecord


class MemoryStore:
    FILES = {
        "episodic": "episodic_memory.jsonl",
        "semantic": "semantic_memory.jsonl",
        "failure": "failure_memory.jsonl",
    }

    def __init__(self, root: Path | str = ".sage_memory"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path_for_kind(self, kind: str) -> Path:
        return self.root / self.FILES.get(kind, f"{kind}_memory.jsonl")

    def write(self, record: MemoryRecord) -> MemoryRecord:
        path = self._path_for_kind(record.kind)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_dict(), sort_keys=True) + "\n")
        return record

    def write_text(
        self,
        kind: str,
        text: str,
        tags: list[str] | None = None,
        source_run_id: str | None = None,
    ) -> MemoryRecord:
        record = MemoryRecord(
            memory_id=str(uuid4()),
            kind=kind,
            text=text,
            tags=tags or [],
            created_at=datetime.now(timezone.utc).isoformat(),
            source_run_id=source_run_id,
        )
        return self.write(record)

    def list(self, kind: str | None = None) -> list[dict]:
        paths = [self._path_for_kind(kind)] if kind else sorted(self.root.glob("*_memory.jsonl"))
        records = []
        for path in paths:
            if not path.exists():
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    records.append(json.loads(line))
        return records

    def search(self, query: str, top_k: int, kind: str | None = None) -> list[dict]:
        return retrieve(query, self.list(kind), ["text", "kind", "tags"], top_k)
