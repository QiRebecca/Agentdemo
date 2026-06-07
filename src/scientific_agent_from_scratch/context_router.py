from __future__ import annotations

from pathlib import Path
from typing import Any

from scientific_agent_from_scratch.rag import retrieve


def load_note_records(notes_root: Path | str = "notes") -> list[dict[str, Any]]:
    root = Path(notes_root)
    records = []
    if not root.exists():
        return records
    for path in sorted(root.glob("*.md")):
        records.append({"id": path.stem, "title": path.stem.replace("_", " "), "path": str(path), "text": path.read_text(encoding="utf-8")})
    return records


class ContextRouter:
    def __init__(self, notes_root: Path | str, memory_store: Any, skill_registry: Any, tool_registry: Any):
        self.documents = load_note_records(notes_root)
        self.memory_store = memory_store
        self.skill_registry = skill_registry
        self.tool_registry = tool_registry

    def retrieve_all(self, query: str, top_k: int = 3) -> dict[str, list[dict[str, Any]]]:
        return {
            "documents": retrieve(query, self.documents, ["title", "text", "path"], top_k),
            "memories": self.memory_store.search(query, top_k) if self.memory_store else [],
            "skills": self.skill_registry.retrieve(query, top_k) if self.skill_registry else [],
            "tools": self.tool_registry.retrieve(query, top_k) if self.tool_registry else [],
        }
