# Agents

This document describes the autonomous agents in this marketplace and how to maintain them.

## Current Agents

### data-pipeline-orchestrator

**File:** `agents/data-pipeline.md`
**Plugin:** mxcp-data-pipeline
**Color:** green
**Model:** inherit

Orchestrates end-to-end Excel-to-MXCP data pipelines by coordinating three skills in sequence:

1. `data-investigation` — profile Excel, test hypotheses, produce `data-model-spec.md`
2. `mxcp-dbt-ingest` — scaffold dbt project, build models, run 6-layer verification
3. `mxcp-expert` — (optional) design SQL/Python endpoints from mart tables

Triggers on requests like "build a data pipeline from Excel", "ingest this spreadsheet into MXCP", or "re-run the pipeline after schema changes" (recovery mode).

## Maintenance Guide

### Agent File Format

Agents live in the `agents/` directory as `.md` files. They are auto-discovered by Claude Code — no manifest entry needed. Each agent file has:

- **YAML frontmatter:** `name`, `description` (with `<example>` blocks), `model`, `color`, `tools`
- **Markdown body:** System prompt defining the agent's behavior

### YAML Frontmatter Rules

- `description` MUST use folded scalar syntax (`description: >`) when it contains `<example>` blocks. Plain strings break YAML parsing because `Context:` inside examples is interpreted as a mapping key.
- `name` must be lowercase with hyphens, 3-50 characters.
- `model` should be `inherit` unless a specific model is required.
- `tools` should follow least-privilege — only list tools the agent actually needs.

### Description Best Practices

- Start with what the agent does and when to trigger it.
- Include 2-4 `<example>` blocks showing user requests and expected assistant responses.
- Each example needs `Context:`, `user:`, `assistant:`, and `<commentary>` explaining why the agent triggers.
- Be specific about when NOT to use the agent (e.g., individual skill tasks vs full pipeline).

### System Prompt Best Practices

- Write in second person ("You are...", "You coordinate...").
- Keep behavior-focused — delegate detailed workflows to skills.
- Define an output format so the agent reports consistently.
- Include error handling guidance (retry/skip/abort pattern).
- Keep under 10,000 characters.

### Adding a New Agent

1. Create `agents/<agent-name>.md` with frontmatter + system prompt.
2. Follow the format of `data-pipeline.md` as a reference.
3. Test triggering by using similar phrasing to the description examples.
4. Review against `plugin-dev:agent-development` skill guidelines.
5. No manifest changes needed — auto-discovery handles registration.

### Updating an Existing Agent

1. Read the current agent file before making changes.
2. If changing the description, ensure examples still match the agent's actual behavior.
3. If the agent delegates to skills, verify the skill names still match.
4. Test triggering after changes — description wording directly affects when Claude activates the agent.

### Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| YAML parse errors from `<example>` blocks | Use `description: >` folded scalar |
| Agent not triggering | Check description examples match user phrasing |
| Agent duplicates skill logic | Keep agent lean — delegate to skills |
| Stale skill references in system prompt | Update when skills are renamed or restructured |
| Over-broad tool access | Remove tools the agent doesn't use |
