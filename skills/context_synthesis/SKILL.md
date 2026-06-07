# Context Synthesis

## Purpose

Turn retrieved documents and memory into compact working context.

## When To Use

Use when a task has retrieval results that need to be summarized before planning or acting.

## Inputs

- `retrieved_context`: dictionary containing documents, memories, skills, and tools.

## Steps

1. Identify the highest scoring document and memory records.
2. Extract the concrete workflow guidance.
3. Keep the summary short.
4. Preserve source names or paths.

## Validation

- The summary mentions sources.
- The summary is short.
