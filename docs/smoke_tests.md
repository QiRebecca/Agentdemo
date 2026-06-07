# Smoke Tests

The test suite is intentionally small and local. It verifies that the runtime boots, exercises the core components, and writes inspectable artifacts.

1. Kernel boot

   Pass condition: `AgentKernel` initializes with registered tools, loaded skills, a default deterministic policy, and can create an initial `AgentState`.

2. RAG router

   Pass condition: a query over the multi-index router returns expected document and skill matches.

3. Memory roundtrip

   Pass condition: an episodic memory record can be written to JSONL and retrieved by keyword.

4. Typed tool call

   Pass condition: `run_calculation` validates input, returns a structured success result for a valid expression, and returns a structured error for invalid input.

5. Architecture tool contracts and manifest

   Pass condition: `validate_skill_contracts` confirms selected skills reference registered tools, and `build_execution_manifest` returns a compact manifest with run counts.

6. Skill activation

   Pass condition: relevant skills can be retrieved from `skills/` and composed into an execution order.

7. End-to-end architecture run

   Pass condition: the kernel run completes, writes all required local artifacts including `execution_manifest.json`, records key trace events, and produces a passing `verification.json`.

8. Policy layer

   Pass condition: the policy factory creates `DeterministicPolicy`, deterministic decisions have the expected shape, and policy metadata appears in `run_config.json`.

Run all smoke tests with:

```bash
python -m pytest -q
```
