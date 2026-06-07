from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scientific_agent_from_scratch import AgentKernel


DEFAULT_GOAL = (
    "Plan and execute a minimal toy computational research workflow: retrieve relevant notes, "
    "select reusable skills, call one typed tool, write a short reproducible report skeleton, "
    "save an episodic memory summary, and emit a structured execution trace."
)


def next_run_dir(root: Path = Path(".sage_runs")) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    index = 1
    while True:
        path = root / f"run_{index:03d}"
        if not path.exists():
            return path
        index += 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the SAGE architecture demo.")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or next_run_dir()
    print("SAGE architecture demo\n")
    kernel = AgentKernel()
    state = kernel.run(DEFAULT_GOAL, run_dir=run_dir)

    steps = [
        "Parsed goal",
        "Built task graph",
        "Retrieved context",
        "Retrieved memory",
        "Selected skills",
        "Executed typed tool call",
        "Wrote report",
        "Wrote memory",
        "Verified run",
    ]
    for index, step in enumerate(steps, start=1):
        print(f"[{index}/9] {step}")

    verification_path = run_dir / "verification.json"
    verification = json.loads(verification_path.read_text(encoding="utf-8")) if verification_path.exists() else {"pass": False}
    print("\nRun completed." if state.status == "completed" else "\nRun failed.")
    print(f"Trace: {run_dir / 'trace.jsonl'}")
    print(f"Report: {run_dir / 'report.md'}")
    print(f"Verification: {'passed' if verification.get('pass') else 'failed'}")
    return 0 if state.status == "completed" and verification.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
