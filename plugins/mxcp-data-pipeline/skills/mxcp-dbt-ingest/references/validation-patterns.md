---
title: "Validation Patterns"
description: "Complete 6-layer verification patterns for Excel-to-DuckDB data pipelines"
---

# Validation Patterns

## Table of Contents

- [Full Verification Sequence](#full-verification-sequence)
- [Layer 1: Self-Validating Profiling](#layer-1-self-validating-profiling)
- [Layer 2: User Review](#layer-2-user-review)
- [Layer 3: dbt Tests](#layer-3-dbt-tests)
- [Layer 4: Row Count Validation](#layer-4-row-count-validation)
- [Layer 5: Checksum Validation](#layer-5-checksum-validation)
- [Layer 6: Sample Comparison](#layer-6-sample-comparison)
- [Auto-Generated dbt Tests](#auto-generated-dbt-tests)
- [Lineage Validation](#lineage-validation)
- [Schema Type Validation](#schema-type-validation)

## Full Verification Sequence

Copy-paste this after every `mxcp dbt run`:

```bash
# Auto-generate dbt tests from spec (review output before running)
python scripts/generate_dbt_tests.py --spec data-model-spec.md

# Install dbt packages (required for dbt_utils tests)
mxcp dbt deps

# Build all models
mxcp dbt run

# Run all dbt tests
mxcp dbt test

# Source-vs-target validation (row count + checksum + sample)
python scripts/validate_post_ingest.py <excel_file> \
    --db data/db-default.duckdb \
    --tables "Sheet1:stg_sheet1,Sheet2:stg_sheet2"

# Schema type validation
python scripts/validate_schema_types.py \
    --db data/db-default.duckdb \
    --spec data-model-spec.md

# Row count lineage validation
python scripts/validate_lineage.py \
    --db data/db-default.duckdb \
    --manifest project-manifest.md

# Create drift baseline
mxcp drift-snapshot
```

## Layer 1: Self-Validating Profiling

Handled by `profile_excel.py`. Every structural assertion is tested against the data during the investigation phase. No manual intervention needed.

## Layer 2: User Review

Present `data-model-spec.md` to the user for review. Optional but recommended for business-critical pipelines.

## Layer 3: dbt Tests

### Standard Tests

```yaml
# models/schema.yml
version: 2
models:
  - name: stg_orders
    columns:
      - name: order_id
        data_tests:
          - not_null
          - unique
      - name: customer_id
        data_tests:
          - not_null
          - relationships:
              to: ref('stg_customers')
              field: customer_id
      - name: status
        data_tests:
          - accepted_values:
              values: ['pending', 'completed', 'cancelled']
```

### Range Constraints

```yaml
      - name: quantity
        data_tests:
          - dbt_utils.expression_is_true:
              expression: ">= 0"
      - name: order_date
        data_tests:
          - dbt_utils.expression_is_true:
              expression: ">= '2020-01-01'"
          - dbt_utils.expression_is_true:
              expression: "<= CURRENT_DATE"
```

### Composite Key Tests

```yaml
  - name: stg_stock_levels
    data_tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns:
            - sku
            - warehouse_id
```

### Custom Aggregate Test

```sql
-- tests/assert_order_totals_match.sql
-- Verify mart total matches staging total
SELECT 1
WHERE (
    SELECT ROUND(SUM(total), 2) FROM {{ ref('mart_orders') }}
) != (
    SELECT ROUND(SUM(total), 2) FROM {{ ref('stg_orders') }}
)
```

## Layer 4: Row Count Validation

Handled by `validate_post_ingest.py`. Compares Excel sheet row count against DuckDB staging table row count.

```
validate_post_ingest.py <excel_file> --db <db> --tables "Sheet:table,..."
```

Expected: row counts match exactly (after dropna on both sides).

## Layer 5: Checksum Validation

Also in `validate_post_ingest.py`. For each column:
- Numeric: compares `SUM()` and `COUNT()` between pandas and DuckDB with float tolerance
- String: compares `COUNT(DISTINCT)` between pandas and DuckDB
- Uses `canonical.values_close()` for tolerance-based comparison

## Layer 6: Sample Comparison

Also in `validate_post_ingest.py`. Compares 50 random rows (seeded for reproducibility):
- Positional matching by index with `ORDER BY rowid` in DuckDB
- Column-by-column comparison with type-aware tolerance
- Reports mismatches with row index, column name, expected vs actual

## Auto-Generated dbt Tests

`generate_dbt_tests.py` reads `data-model-spec.md` and produces schema YAML:

```bash
python scripts/generate_dbt_tests.py --spec data-model-spec.md
```

Generates:
- `not_null` for columns with `Nullable: no`
- `unique` for columns marked as primary keys
- `accepted_values` for enum columns
- `relationships` for verified FK columns
- `dbt_utils.expression_is_true` for range constraints (min/max from spec)
- Quotes non-numeric range values (dates, strings) for DuckDB compatibility
- Normalizes column names to snake_case via `canonical.normalize_column_name()`

**Always review the generated YAML before running `mxcp dbt test`.**

## Lineage Validation

`validate_lineage.py` reads the Row Count Lineage table from `project-manifest.md`:

```bash
python scripts/validate_lineage.py --db <db> --manifest project-manifest.md
```

Checks:
- Expected row counts match actual DuckDB row counts per table
- WHERE filters are documented with expected row reduction
- Aggregate sums match across layers (source table SUM vs mart table SUM)
- Case-insensitive table name matching for DuckDB compatibility

## Schema Type Validation

`validate_schema_types.py` compares DuckDB actual types against spec expected types:

```bash
python scripts/validate_schema_types.py --db <db> --spec data-model-spec.md
```

Type mapping:
- `integer` → INTEGER, BIGINT, SMALLINT, TINYINT, INT, HUGEINT
- `number` → DOUBLE, FLOAT, DECIMAL, REAL, NUMERIC
- `string` → VARCHAR, TEXT, CHAR, BLOB
- `datetime` → TIMESTAMP, DATE, TIME, TIMESTAMP_S, TIMESTAMP_MS, TIMESTAMP_NS
- `boolean` → BOOLEAN, BOOL

Normalizes DuckDB types by stripping precision/scale (e.g., `DECIMAL(18,2)` → `DECIMAL`).
