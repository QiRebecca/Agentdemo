from pathlib import Path

from scientific_agent_from_scratch.context_router import ContextRouter, load_note_records
from scientific_agent_from_scratch.memory import MemoryStore
from scientific_agent_from_scratch.skills import SkillRegistry
from scientific_agent_from_scratch.tools import ToolRegistry


ROOT = Path(__file__).resolve().parents[1]


def test_rag_router(tmp_path):
    memory = MemoryStore(tmp_path / "memory")
    skills = SkillRegistry(ROOT / "skills")
    docs = load_note_records(ROOT / "notes")
    tools = ToolRegistry(document_records=docs, memory_store=memory, skill_registry=skills)
    router = ContextRouter(ROOT / "notes", memory, skills, tools)
    results = router.retrieve_all("reproducible workflow report")
    doc_ids = {record["id"] for record in results["documents"]}
    skill_names = {record["name"] for record in results["skills"]}
    assert {"reproducible_workflows", "report_structure"} & doc_ids
    assert {"report_writing", "context_synthesis"} & skill_names
