---
name: mxcp-dbt-ingest
description: "This skill should be used when the user asks to 'ingest data with dbt', 'create dbt models for Excel', 'load Excel into DuckDB', 'create staging models', 'set up dbt transformations', or mentions dbt ingestion, staging/marts layers, or Excel-to-DuckDB workflows. Requires an existing data-model-spec.md (produced by the data-investigation skill). For end-to-end pipeline requests, use the data-pipeline-workflow skill instead."
---

# MXCP dbt Ingest

Build a verified dbt pipeline from `data-model-spec.md` to DuckDB, with 6-layer validation.

## Prerequisites

- `data-model-spec.md` must exist (produced by `data-investigation` skill). If missing, run investigation first.
- `mxcp` CLI installed (`mxcp --version`)
- Python with pandas, openpyxl, numpy, duckdb

## Template Setup

1. Copy the `excel-to-mxcp` template from this skill's assets:
```bash
cp -R <skill-assets>/project-templates/excel-to-mxcp/. ./
```

2. Rename the project in 3 files:
- `mxcp-site.yml`: update `name:` field
- `dbt_project.yml`: update `name:` and `profile:` fields
- `mxcp-config.yml`: update the `projects: mxcp-template:` key to match

3. Verify all required scripts exist after template copy:
   - `scripts/profile_excel.py`, `scripts/canonical.py`
   - `scripts/generate_dbt_tests.py`
   - `scripts/validate_post_ingest.py`, `scripts/validate_pre_ingest.py`
   - `scripts/validate_schema_types.py`, `scripts/validate_lineage.py`

4. Copy your Excel file into `source_files/`

## Pipeline Layers

### 1. dbt Python Models — Excel Loading

One Python model per sheet in `models/staging/`. Pattern:

```python
# models/staging/stg_orders.py
import pandas as pd

def model(dbt, session):
    df = pd.read_excel("source_files/data.xlsx", sheet_name="Orders", header=0)
    df = df.dropna(how="all").dropna(axis=1, how="all")
    # Normalize column names
    df.columns = [c.strip().lower().replace(' ', '_').replace('-', '_') for c in df.columns]
    return df
```

For complex cases, read the reference files:
- **Merged cells:** See `references/merged-cells.md` — use openpyxl to unmerge and forward-fill
- **Transposed tables:** See `references/transposition.md` — use pandas.melt() to unpivot
- **Large files (50MB+):** Use openpyxl read-only mode with chunked reading

### 2. Staging SQL Models

One SQL model per source table. Normalize, cast, clean:

```sql
-- models/staging/stg_orders.sql
{{ config(materialized='table') }}

SELECT
    CAST(order_id AS INTEGER) AS order_id,
    CAST(customer_id AS INTEGER) AS customer_id,
    CAST(order_date AS DATE) AS order_date,
    CAST(quantity AS INTEGER) AS quantity,
    CAST(unit_price AS DOUBLE) AS unit_price,
    -- NULLIF for empty-string columns (from data-model-spec empty_string_count > 0)
    NULLIF(TRIM(notes), '') AS notes,
    CAST(total AS DOUBLE) AS total
FROM {{ ref('stg_orders_raw') }}
WHERE order_id IS NOT NULL
```

**Empty string handling:** For every column flagged with `empty_string_count > 0` in the data-model-spec, wrap with `NULLIF(TRIM(column_name), '')`.

### 3. Intermediate Models

Join tables following relationships from data-model-spec:

```sql
-- models/intermediate/int_orders_enriched.sql
{{ config(materialized='table') }}

SELECT
    o.*,
    c.name AS customer_name,
    c.tier AS customer_tier,
    p.product_name,
    p.category
FROM {{ ref('stg_orders') }} o
LEFT JOIN {{ ref('stg_customers') }} c ON o.customer_id = c.customer_id
LEFT JOIN {{ ref('stg_products') }} p ON o.product_id = p.product_id
```

### 4. Marts — AI-Ready Tables

Flatten for LLM consumption. Add computed columns:

```sql
-- models/marts/mart_orders.sql
{{ config(materialized='table') }}

SELECT
    o.order_id,
    o.order_date,
    o.customer_name,
    o.customer_tier,
    o.product_name,
    o.category,
    o.quantity,
    o.unit_price,
    o.total,
    o.total / NULLIF(o.quantity, 0) AS effective_price
FROM {{ ref('int_orders_enriched') }} o
```

## dbt Tests

Generate tests from data-model-spec verified assertions:

```bash
python scripts/generate_dbt_tests.py --spec data-model-spec.md
```

This produces a schema.yml with not_null, unique, accepted_values, relationships, range checks (`dbt_utils.expression_is_true`), and composite key tests (`dbt_utils.unique_combination_of_columns`). **Review the generated YAML before running.**

## Deriving Table Mappings

Before running validation, derive `--tables` from `data-model-spec.md`. Extract each sheet's `**Target table:**` value:

```
# Example: data-model-spec.md contains:
#   ## Sheet: Orders  →  **Target table:** stg_orders
#   ## Sheet: Products →  **Target table:** stg_products
# Result: --tables "Orders:stg_orders,Products:stg_products"
```

## Running and Verifying (6 Layers)

Execute the full verification sequence:

```bash
# 1. Generate dbt tests from spec
python scripts/generate_dbt_tests.py --spec data-model-spec.md

# 2. Install dbt packages (required for dbt_utils tests)
mxcp dbt deps

# 3. Build all models
mxcp dbt run

# 4. Run dbt tests (layer 3: schema tests)
mxcp dbt test

# 5. Source-vs-target validation (layers 4-6: row count, checksum, sample)
#    Use the derived table mappings from data-model-spec.md
python scripts/validate_post_ingest.py <excel_file> \
    --db data/db-default.duckdb \
    --tables "Orders:stg_orders,Products:stg_products"

# 6. Schema type validation
python scripts/validate_schema_types.py \
    --db data/db-default.duckdb \
    --spec data-model-spec.md
```

**IMPORTANT:** Write `project-manifest.md` NOW (see below), BEFORE running lineage validation.

```bash
# 7. Row count lineage validation (requires manifest — run AFTER writing project-manifest.md)
python scripts/validate_lineage.py \
    --db data/db-default.duckdb \
    --manifest project-manifest.md

# 8. Create drift baseline
mxcp drift-snapshot
```

See `references/validation-patterns.md` for detailed patterns and `references/drift-detection.md` for ongoing monitoring.

## WHERE Filter Enforcement

Every SQL model with a WHERE clause MUST document it in `project-manifest.md`:

```markdown
### Documented Filters
| Model | Filter | Expected Reduction |
|-------|--------|--------------------|
| stg_orders | WHERE order_id IS NOT NULL | removes ~5 rows from 45231 |
| int_orders | WHERE status != 'deleted' | removes ~200 rows from 45226 |
```

`validate_lineage.py` flags undocumented row reductions.

## Writing project-manifest.md

Write `project-manifest.md` after layers 1-6 pass but **BEFORE** running lineage validation (`validate_lineage.py`). Include:
- Source file metadata (path, size, MD5, sheet-to-table mappings)
- Cleaning decisions made and rationale
- Expected schema per table
- Source-vs-target checksums
- **Row Count Lineage** table (read by `validate_lineage.py`):

```markdown
### Row Count Lineage
| Layer | Table | Expected Rows | Filter | Reduction |
|-------|-------|---------------|--------|-----------|
| staging | stg_orders | 45231 | - | - |
| intermediate | int_orders | 45031 | WHERE status != 'deleted' | -200 |
| mart | mart_orders | 45031 | - | - |

### Aggregate Checks
| Column | Source Table | Mart Table | Expected Sum |
|--------|-------------|------------|-------------|
| total | stg_orders | mart_orders | 1234567.89 |
```

## Failure Recovery

When a subsequent run fails because the Excel changed:

1. Read `project-manifest.md` to understand original build decisions
2. Run `python scripts/validate_pre_ingest.py <new_excel> --manifest project-manifest.md` to detect structural changes
3. Run `python scripts/profile_excel.py <new_excel>` and compare against manifest
4. Update dbt models + tests for any schema changes
5. Re-run full verification sequence
6. Update `project-manifest.md` with new schema
