# Extension Points

SAGE is intentionally organized around clear runtime boundaries. The current implementation is local and reproducible, while the architecture can be extended in several directions.

## Web And Document Ingestion

External content can be converted into local document records and routed through the existing `ContextRouter`. A future `WebDocumentLoader`, `URLIngestTool`, or PDF loader can normalize external content into the same record format used by `notes/*.md`.

## Executable Skill Graphs

Current skills are procedural memory units loaded from `manifest.json` and `SKILL.md`. A future skill executor can extend manifests with structured steps such as:

```json
{
  "steps": [
    {"tool": "search_docs", "args_from": "goal"},
    {"tool": "build_execution_manifest", "args_from": "state"}
  ]
}
```

These steps can bind to `ToolRegistry` actions while preserving typed validation and trace logging.

## Model-Backed Planning

The policy layer can replace deterministic choices for goal refinement, skill selection, tool planning, report drafting, and memory summarization. The runtime boundary remains the same: policies propose decisions, while the kernel executes validated actions and writes traces.

## Permissioned Tools

`ToolSpec.permission` can be extended into explicit scopes such as:

- `read`
- `write_run_dir`
- `network`
- `execute_local`

This allows future tools to be added without weakening inspection or traceability.

## Persistent Indexes

The document index can be extended from static `notes/*.md` into `.sage_indexes/documents.jsonl`, allowing web pages, PDFs, markdown, and prior run summaries to share one retrieval interface.
