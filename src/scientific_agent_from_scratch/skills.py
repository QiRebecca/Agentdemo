from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scientific_agent_from_scratch.rag import retrieve
from scientific_agent_from_scratch.state import SkillSpec


class SkillRegistry:
    def __init__(self, root: Path | str = "skills"):
        self.root = Path(root)
        self.skills: dict[str, SkillSpec] = {}
        self.load()

    def load(self) -> None:
        self.skills.clear()
        if not self.root.exists():
            return
        for manifest_path in sorted(self.root.glob("*/manifest.json")):
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            skill_path = manifest_path.parent / "SKILL.md"
            spec = SkillSpec(
                name=data["name"],
                description=data["description"],
                when_to_use=data["when_to_use"],
                required_tools=list(data.get("required_tools", [])),
                inputs=dict(data.get("inputs", {})),
                outputs=dict(data.get("outputs", {})),
                validation=list(data.get("validation", [])),
                path=str(skill_path),
            )
            self.skills[spec.name] = spec

    def list(self) -> list[dict[str, Any]]:
        return [skill.to_dict() for skill in self.skills.values()]

    def retrieve(self, query: str, top_k: int = 4) -> list[dict[str, Any]]:
        return retrieve(query, self.list(), ["name", "description", "when_to_use"], top_k)

    def compose_skills(self, selected: list[dict[str, Any]]) -> dict[str, Any]:
        preferred = ["context_synthesis", "tool_execution", "report_writing", "memory_update"]
        names = {item["name"] for item in selected}
        order = [name for name in preferred if name in names]
        order.extend(sorted(names - set(order)))
        edges = [[order[index], order[index + 1]] for index in range(len(order) - 1)]
        return {"composition_order": order, "edges": edges}
