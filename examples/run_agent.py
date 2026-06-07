from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scientific_agent_from_scratch import AgentKernel


DEFAULT_GOAL = (
    "Run a concise agent workflow: retrieve local context, select relevant skills, "
    "plan and execute a safe typed tool sequence, write a report, store memory, "
    "and verify all run artifacts."
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
    parser = argparse.ArgumentParser(description="Run SAGE with a selected policy backend.")
    parser.add_argument("--goal", default=DEFAULT_GOAL)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--policy", choices=["deterministic", "openai", "openai-chat"], default="deterministic")
    parser.add_argument("--model", default=None, help="Optional model name for model-backed policies.")
    parser.add_argument("--base-url", default=None, help="Optional base URL for --policy openai-chat.")
    args = parser.parse_args()

    run_dir = args.run_dir or next_run_dir()
    kernel = AgentKernel(policy_backend=args.policy, model=args.model, base_url=args.base_url)
    state = kernel.run(args.goal, run_dir=run_dir)

    verification_path = run_dir / "verification.json"
    verification = json.loads(verification_path.read_text(encoding="utf-8")) if verification_path.exists() else {"pass": False}

    print("SAGE agent run")
    print(f"Policy: {args.policy}")
    if args.model:
        print(f"Model: {args.model}")
    if args.base_url:
        print(f"Base URL: {args.base_url}")
    print(f"Status: {state.status}")
    print(f"Trace: {run_dir / 'trace.jsonl'}")
    print(f"Report: {run_dir / 'report.md'}")
    print(f"Verification: {'passed' if verification.get('pass') else 'failed'}")
    return 0 if state.status == "completed" and verification.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
