# Skills

In SAGE, skills are treated as lightweight procedural memory: reusable task procedures that can be retrieved, activated, and composed.

Each skill lives in a directory under `skills/`:

```text
skills/<skill_name>/
  manifest.json
  SKILL.md
```

## `manifest.json`

The manifest is machine-readable metadata used by `SkillRegistry`:

- `name`: stable skill identifier.
- `description`: short summary for retrieval.
- `when_to_use`: activation guidance used during keyword retrieval.
- `required_tools`: tools the skill expects to be available.
- `inputs`: input contract.
- `outputs`: output contract.
- `validation`: lightweight checks the runtime or reviewer can inspect.

## `SKILL.md`

`SKILL.md` is the human-readable procedure. It explains purpose, usage conditions, expected inputs, execution steps, and validation notes. The demo does not execute markdown as code; it treats the file as inspectable procedural knowledge.

## Retrieval And Composition

Skill retrieval uses keyword overlap over `name`, `description`, and `when_to_use`. Selected skills are then composed into a deterministic ordered plan. For the architecture demo, the intended order is:

```text
context_synthesis -> tool_execution -> report_writing -> memory_update
```

This composition is written to `selected_skills.json` so reviewers can inspect which reusable procedures were activated.

## Included Skills

- `context_synthesis`: summarize retrieved notes and memory into compact task context.
- `tool_execution`: plan and execute typed architecture tools with validated inputs.
- `report_writing`: write a concise reproducible report from context, skills, tools, and trace.
- `memory_update`: store a short episodic memory summarizing a completed run.
