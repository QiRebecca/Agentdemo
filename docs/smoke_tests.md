# Smoke Tests

The test suite is intentionally small and local. It verifies that the architecture demo boots, exercises the core runtime components, and writes inspectable artifacts.

1. Kernel boot

   Pass condition: `AgentKernel` initializes with registered tools and loaded skills, and can create an initial `AgentState`.

2. RAG router

   Pass condition: a query over the multi-index router returns expected document and skill matches.

3. Memory roundtrip

   Pass condition: an episodic memory record can be written to JSONL and retrieved by keyword.

4. Tool call

   Pass condition: `run_calculation` validates input, returns a structured success result for a valid expression, and returns a structured error for invalid input.

5. Skill activation

   Pass condition: relevant skills can be retrieved from `skills/` and composed into an execution order.

6. End-to-end architecture demo

   Pass condition: the kernel run completes, writes all required local artifacts, records key trace events, and produces a passing `verification.json`.

Run all smoke tests with:

```bash
python -m pytest -q
```
