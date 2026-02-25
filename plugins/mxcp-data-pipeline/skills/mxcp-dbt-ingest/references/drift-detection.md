---
title: "Drift Detection"
description: "Patterns for detecting and handling data drift in Excel-to-MXCP pipelines"
---

# Drift Detection

## Table of Contents

- [Baseline Creation](#baseline-creation)
- [Drift Checking](#drift-checking)
- [Pre-Ingest Validation](#pre-ingest-validation)
- [Incremental/Append Load Patterns](#incrementalappend-load-patterns)
- [Stale Data Detection](#stale-data-detection)

## Baseline Creation

After a successful verification run, create a drift baseline:

```bash
mxcp drift-snapshot
```

This saves the current schema fingerprint (table names, column names, column types, row counts) to the `drift/` directory.

## Drift Checking

Before re-running the pipeline with a new Excel file:

```bash
mxcp drift-check
```

This compares the current database schema against the baseline and reports:
- New tables/columns added
- Tables/columns removed
- Type changes
- Significant row count changes

## Pre-Ingest Validation

Run the pre-ingest validator before loading a new version of the Excel file:

```bash
python scripts/validate_pre_ingest.py <new_excel_file> --manifest project-manifest.md
```

This checks:
- Sheet names match (detects renamed/added/removed sheets)
- Column names match (with fuzzy rename detection via Levenshtein distance)
- Column types are compatible (detects type drift)
- Row counts are in expected range (flags significant changes)

Exit codes:
- `0` — no structural changes, safe to re-run
- `1` — structural changes detected, review before proceeding
- `2` — critical errors (missing sheets, major schema changes)

## Incremental/Append Load Patterns

### When to Use Full Reload vs Incremental

**Full reload (default, recommended for Excel):**
- Simpler, safer, complete
- Use `{{ config(materialized='table') }}` — inherently idempotent
- Re-ingests the entire Excel file every time
- No deduplication needed

**Incremental (only when explicitly needed):**
- File grows monotonically (new rows appended, old rows unchanged)
- File is too large for full reload (>100MB)
- User explicitly requests incremental loading

### Deduplication Warnings

If using `df.to_sql` with `if_exists='append'` (incremental), duplicate rows WILL occur unless you deduplicate. **Always use `if_exists='replace'` for full-reload (the default).**

For incremental loads, add deduplication in staging:

```sql
{{ config(materialized='incremental', unique_key='order_id') }}

SELECT *
FROM {{ ref('stg_orders_raw') }}
{% if is_incremental() %}
    WHERE _loaded_at > (SELECT MAX(_loaded_at) FROM {{ this }})
{% endif %}
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY order_id
    ORDER BY _loaded_at DESC
) = 1
```

### Idempotent Reload Pattern

`{{ config(materialized='table') }}` replaces the full table on every run. This is:
- Idempotent — running twice produces the same result
- Safe — no duplicate accumulation
- Simple — no incremental logic needed

This is the recommended default for Excel-to-DuckDB pipelines.

## Stale Data Detection

Detect when a file has been updated but the data hasn't changed:

```python
import os
from datetime import datetime

# Compare file modification time against max date in data
file_mtime = datetime.fromtimestamp(os.path.getmtime("source_files/data.xlsx"))
max_date = con.execute("SELECT MAX(order_date) FROM stg_orders").fetchone()[0]

if file_mtime > max_date:
    print(f"WARNING: File modified {file_mtime} but latest data is {max_date}")
    print("The file may contain unchanged data or updates to non-date columns")
```

This helps detect:
- Files that were re-exported but contain the same data
- Files that were modified (metadata changes) without data changes
- Partial updates where only some sheets were refreshed
