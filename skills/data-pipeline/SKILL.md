---
name: data-pipeline
description: "This skill should be used when the user asks to 'build a data pipeline from Excel', 'ingest Excel into MXCP', 'create an MXCP project from a spreadsheet', 'set up the full data pipeline', or mentions end-to-end Excel-to-MXCP workflows. Orchestrates investigation, dbt ingestion, and endpoint creation phases."
---

# Data Pipeline Orchestrator

End-to-end Excel-to-MXCP pipeline: investigation → dbt ingestion → endpoint design.

## Prerequisites Check

Before starting, verify:
1. Excel file path exists and is readable
2. `mxcp --version` succeeds
3. Check if `mxcp-expert` skill is available — if not, Phase 3 (endpoint design) will be skipped

## Phase 1: Data Investigation

Invoke the `data-investigation` skill:

1. Ask the user for the Excel file path
2. Run `python scripts/profile_excel.py <excel_file> --output data-profile-report.md`
3. Read the profile report and match against domain patterns
4. Test every hypothesis (FK match rates, calculated columns, unique constraints)
5. Write `data-model-spec.md` (must follow format in data-investigation's `references/data-model-spec-format.md`)
6. Present summary to user: sheet count, row counts, detected relationships, flagged unknowns
7. Ask if they want to proceed to Phase 2

## Phase 2: dbt Ingestion

Invoke the `mxcp-dbt-ingest` skill:

1. Read `data-model-spec.md`
2. Scaffold project from `excel-to-mxcp` template
3. Generate dbt Python models (one per sheet) + SQL staging/intermediate/mart models
4. Generate dbt tests from spec: `python scripts/generate_dbt_tests.py --spec data-model-spec.md`
5. Run full verification:
   ```
   mxcp dbt deps
   mxcp dbt run
   mxcp dbt test
   python scripts/validate_post_ingest.py <excel> --db data/db-default.duckdb --tables "<mappings>"
   python scripts/validate_schema_types.py --db data/db-default.duckdb --spec data-model-spec.md
   python scripts/validate_lineage.py --db data/db-default.duckdb --manifest project-manifest.md
   mxcp drift-snapshot
   ```
6. Write `project-manifest.md` with all build decisions and verification results
7. Report results to user

## Phase 3: Endpoint Design (if mxcp-expert available)

Invoke the `mxcp-expert` skill:

1. Design SQL/Python tools based on mart tables
2. Create resources for data access patterns
3. Add prompts for common analysis workflows
4. Run `mxcp validate`, `mxcp test`, `mxcp lint`

If `mxcp-expert` is not installed, skip this phase and tell the user to create endpoints manually using MXCP documentation.

## Error Handling

At any phase failure:
- Report the error clearly (which phase, which step, full error output)
- Ask user how to proceed: retry, skip phase, or abort
- Do NOT proceed to the next phase until the current phase passes all validations

## Failure Recovery Mode

When called on an existing project (check for `project-manifest.md`):

1. Read `project-manifest.md` to understand original build decisions
2. Run `python scripts/validate_pre_ingest.py <new_excel> --manifest project-manifest.md` to detect structural changes
3. Run `python scripts/profile_excel.py <new_excel>` and compare against manifest
4. Update dbt models + tests for schema changes
5. Re-run full verification sequence
6. Update `project-manifest.md` with new schema

## Ralph Loop Integration (Optional)

For complex Excel files (5+ sheets, 50+ columns), Phase 2 can benefit from autonomous iteration. If the `ralph-loop` plugin is installed:

```
/ralph-loop "Read data-model-spec.md. Generate dbt models following the mxcp-dbt-ingest skill workflow. Run mxcp dbt deps, then mxcp dbt run + mxcp dbt test. Run validation scripts: python scripts/validate_post_ingest.py <excel_file> --db data/db-default.duckdb --tables '<mappings>', python scripts/validate_schema_types.py --db data/db-default.duckdb --spec data-model-spec.md, python scripts/validate_lineage.py --db data/db-default.duckdb --manifest project-manifest.md. Fix failures and re-run until all pass. When ALL pass, output <promise>ALL_VALIDATIONS_PASS</promise>." --completion-promise "ALL_VALIDATIONS_PASS" --max-iterations 30
```

Not recommended for Phase 1 (single-pass) or Phase 3 (needs user interaction).
