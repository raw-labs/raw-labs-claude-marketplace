---
name: data-pipeline-workflow
description: "This skill should be used when the user asks to 'build a data pipeline from Excel', 'ingest Excel into MXCP', 'create an MXCP project from a spreadsheet', 'set up the full data pipeline', or mentions end-to-end Excel-to-MXCP workflows. Orchestrates investigation, dbt ingestion, and endpoint creation phases."
---

# Data Pipeline Orchestrator

End-to-end Excel-to-MXCP pipeline: investigation → dbt ingestion → endpoint design.

This skill follows the same workflow as the `data-pipeline-orchestrator` agent. The canonical orchestration logic lives in the agent definition — refer to it for the full specification.

## Prerequisites Check

Before starting, verify:
1. Excel file path exists and is readable
2. `mxcp --version` succeeds
3. Check if `mxcp-expert` skill is available — if not, Phase 3 (endpoint design) will be skipped
4. Check for existing `project-manifest.md` to determine fresh build vs. recovery mode

## Phase 1: Data Investigation

Invoke the `data-investigation` skill:

1. Ask the user for the Excel file path
2. Ensure profiler is available — if `scripts/profile_excel.py` does not exist, copy from `data-investigation` skill assets first
3. Run `python scripts/profile_excel.py <excel_file> --output data-profile-report.md`
4. Read the profile report and match against domain patterns
5. Test every hypothesis (FK match rates, calculated columns, unique constraints)
6. Write `data-model-spec.md` (must follow format in data-investigation's `references/data-model-spec-format.md`)
7. Present summary to user: sheet count, row counts, detected relationships, flagged unknowns
8. Ask if they want to proceed to Phase 2

## Phase 2: dbt Ingestion

Invoke the `mxcp-dbt-ingest` skill:

1. Read `data-model-spec.md`
2. Scaffold project from `excel-to-mxcp` template
3. Verify all required scripts exist: `generate_dbt_tests.py`, `validate_post_ingest.py`, `validate_schema_types.py`, `validate_lineage.py`, `validate_pre_ingest.py`
4. Generate dbt Python models (one per sheet) + SQL staging/intermediate/mart models
5. Generate dbt tests: `python scripts/generate_dbt_tests.py --spec data-model-spec.md`
6. Derive table mappings from `data-model-spec.md` — extract each sheet's `**Target table:**` value to build the `--tables` argument (e.g., `"Orders:stg_orders,Products:stg_products"`)
7. Run verification layers 1-5:
   ```
   mxcp dbt deps
   mxcp dbt run
   mxcp dbt test
   python scripts/validate_post_ingest.py <excel> --db data/db-default.duckdb --tables "Orders:stg_orders,Products:stg_products"
   python scripts/validate_schema_types.py --db data/db-default.duckdb --spec data-model-spec.md
   ```
8. Write `project-manifest.md` with build decisions, row count lineage, and verification results (**must happen before lineage validation**)
9. Run lineage validation (layer 6 — requires manifest):
   ```
   python scripts/validate_lineage.py --db data/db-default.duckdb --manifest project-manifest.md
   ```
10. Create drift baseline: `mxcp drift-snapshot`
11. Report results to user

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
- Ask user how to proceed: **retry**, **skip phase** (with acknowledgment that downstream phases may be limited), or **abort**
- Record any skipped phases in `project-manifest.md` under `### Skipped Phases`
- If skipping, warn about dependencies on the skipped phase before proceeding

## Failure Recovery Mode

When called on an existing project (check for `project-manifest.md`):

1. Read `project-manifest.md` to understand original build decisions
2. Run `python scripts/validate_pre_ingest.py <new_excel> --manifest project-manifest.md` to detect structural changes
3. Run `python scripts/profile_excel.py <new_excel>` and compare against manifest
4. Update dbt models + tests for schema changes
5. Re-run full verification sequence
6. Update `project-manifest.md` with new schema

## Ralph Loop Integration (Optional)

For complex Excel files (multiple sheets, high column density, or known data quality issues), Phase 2 can benefit from autonomous iteration. If the `ralph-loop` plugin is installed:

```
/ralph-loop "Read data-model-spec.md. Generate dbt models following the mxcp-dbt-ingest skill workflow. Run mxcp dbt deps, then mxcp dbt run + mxcp dbt test. Derive table mappings from data-model-spec.md Target table entries. Run validation scripts. Fix failures and re-run until all pass. When ALL pass, output <promise>ALL_VALIDATIONS_PASS</promise>." --completion-promise "ALL_VALIDATIONS_PASS" --max-iterations 30
```

Not recommended for Phase 1 (single-pass) or Phase 3 (needs user interaction).
