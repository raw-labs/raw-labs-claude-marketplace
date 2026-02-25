---
name: data-pipeline-workflow
description: "This skill should be used when the user asks to 'build a data pipeline from Excel', 'ingest Excel into MXCP', 'create an MXCP project from a spreadsheet', 'set up the full data pipeline', or mentions end-to-end Excel-to-MXCP workflows. Orchestrates investigation, dbt ingestion, and endpoint creation phases."
---

# Data Pipeline Orchestrator

End-to-end Excel-to-MXCP pipeline: investigation → dbt ingestion → endpoint design.

## Workflow

Three phases, executed in order:

1. **Investigation** — invoke `data-investigation` skill to profile Excel, test hypotheses, produce `data-model-spec.md`
2. **dbt Ingestion** — invoke `mxcp-dbt-ingest` skill to scaffold project, build models, run 6-layer verification, write `project-manifest.md`
3. **Endpoint Design** (optional) — invoke `mxcp-expert` skill to create SQL/Python tools from mart tables

## Before Starting

- Verify Excel file path exists and is readable
- Verify `mxcp --version` succeeds
- Check if `project-manifest.md` exists → if yes, enter **recovery mode** (re-profile, detect drift, update models)
- If `scripts/profile_excel.py` is not in the working directory, copy from `data-investigation` skill assets

## Key Rules

- Get user approval after Phase 1 before proceeding to Phase 2
- Derive `--tables` mappings from `data-model-spec.md` `**Target table:**` entries — never use placeholders
- Write `project-manifest.md` BEFORE running `validate_lineage.py`
- On failure: report clearly, offer retry/skip/abort — record skipped phases in manifest
- If `mxcp-expert` is not available, skip Phase 3 and inform the user

## Ralph Loop (Optional)

For complex files (multiple sheets, high column density), Phase 2 benefits from autonomous iteration via `ralph-loop` plugin if installed. Not recommended for Phase 1 (single-pass) or Phase 3 (needs user interaction).

## Detailed Specification

Each phase's detailed workflow, commands, and patterns are documented in the respective skills:
- `data-investigation` — profiling methodology, hypothesis testing, spec format
- `mxcp-dbt-ingest` — template setup, pipeline layers, verification sequence, manifest format
- `mxcp-expert` — endpoint design patterns
