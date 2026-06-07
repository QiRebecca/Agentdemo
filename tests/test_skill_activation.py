from pathlib import Path

from scientific_agent_from_scratch.skills import SkillRegistry


ROOT = Path(__file__).resolve().parents[1]


def test_skill_activation():
    registry = SkillRegistry(ROOT / "skills")
    selected = registry.retrieve("write reproducible report", top_k=4)
    assert "report_writing" in {skill["name"] for skill in selected}
    composition = registry.compose_skills(selected)
    assert composition["composition_order"]
    assert "report_writing" in composition["composition_order"]
