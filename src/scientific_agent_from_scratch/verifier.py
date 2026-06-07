from __future__ import annotations

import json
from pathlib import Path


def verify_run_artifacts(run_dir: Path | str, required_files: list[str]) -> dict:
    run_path = Path(run_dir)
    missing = []
    checked = []
    invalid_json = []
    json_files = {
        "run_config.json",
        "task_graph.json",
        "retrieved_context.json",
        "selected_skills.json",
        "execution_manifest.json",
        "verification.json",
    }
    for name in required_files:
        path = run_path / name
        checked.append(name)
        if not path.exists():
            missing.append(name)
            continue
        if name in json_files:
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                invalid_json.append(name)
    return {
        "pass": not missing and not invalid_json,
        "missing_files": missing,
        "checked_files": checked,
        "invalid_json": invalid_json,
    }
