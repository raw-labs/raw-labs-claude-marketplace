---
title: "data-model-spec.md Format Specification"
description: "Formal contract between the data-investigation and mxcp-dbt-ingest skills"
---

# data-model-spec.md Format

This document defines the exact structure for `data-model-spec.md`. The investigation skill writes this file; the dbt-ingest skill reads it.

## Required Sections

### 1. Header

```markdown
# Data Model Specification

**Source file:** `<path>`
**File size:** <size> MB
**MD5:** `<hash>`
**Generated at:** <timestamp>
**Domain match:** <domain or "none"> (confidence: <high/medium/low>)
```

### 2. Per-Sheet Section (one per sheet)

```markdown
## Sheet: <SheetName>

**Rows:** <count> | **Columns:** <count>
**Target table:** <staging_table_name>
**Header row:** <1-indexed row number> (if not row 1, note skipped title rows)

### Schema

| Column | Type | Nullable | Empty Strings | Notes |
|--------|------|----------|---------------|-------|
| <name> | string/integer/number/datetime/boolean | yes/no | <count> | <enum values, FK ref, format notes> |

### Cleaning Required

- <list of cleaning operations: normalize headers, fix dates, handle merged cells, NULLIF empty strings, etc.>

### Verified Assertions

FK verification thresholds:
- >= 99% match rate: VERIFIED
- 95-99% match rate: VERIFIED WITH WARNINGS (list orphans)
- 80-95% match rate: POSSIBLE (needs review)
- < 80% match rate: NOT A FK

- FK: <column> → <Sheet>.<column> — <VERIFIED|WARNING|POSSIBLE> (match rate: <X>%, orphans: <N>)
- Calculated: <column> = <formula> (match rate: <X>%, mismatches: <N>, diagnosis: <rounding|formula_error|review_needed>)
- Unique: <column> (verified: <count> unique of <count> total)
- Not null: <column> (null rate: 0%)
- Range: <column> (min: <X>, max: <Y>, all positive: <yes/no>)
```

### 3. Cross-Sheet Relationships

```markdown
## Relationships

| From | To | Type | Match Rate | Orphans |
|------|-----|------|-----------|---------|
| <Sheet>.<col> | <Sheet>.<col> | FK | <X>% | <N> |
```

### 4. Flagged Unknowns

```markdown
## Assumptions

These are unverified assumptions the pipeline will use. Override if incorrect:

- <Sheet>.<column>: Enum values [A, B, C] — meanings assumed from context
- <Sheet>: Date column appears to be fiscal year (April-March), not calendar year
```

## Complete Example

```markdown
# Data Model Specification

**Source file:** `source_files/sales_data.xlsx`
**File size:** 12.3 MB
**MD5:** `a1b2c3d4e5f6`
**Generated at:** 2026-02-25T14:30:00
**Domain match:** sales (confidence: high)

## Sheet: Orders

**Rows:** 45231 | **Columns:** 7
**Target table:** stg_orders

### Schema

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| order_id | integer | no | Primary key |
| customer_id | integer | no | FK → Customers.customer_id |
| order_date | datetime | no | Range: 2023-01-01 to 2024-12-31 |
| product_id | integer | no | FK → Products.product_id |
| quantity | integer | no | Range: 1-500 |
| unit_price | number | no | Range: 0.50-9999.99 |
| total | number | no | Calculated: quantity * unit_price |

### Cleaning Required

- Normalize headers (mixed case → snake_case)
- Convert Excel date serial numbers to datetime

### Verified Assertions

- FK: customer_id → Customers.customer_id (match rate: 100%, orphans: 0)
- FK: product_id → Products.product_id (match rate: 99.8%, orphans: 3)
- Calculated: total = quantity * unit_price (match rate: 99.9%, mismatches: 5)
- Unique: order_id (verified: 45231 unique of 45231 total)
- Not null: order_id, customer_id, order_date (null rate: 0%)

## Sheet: Customers

**Rows:** 1200 | **Columns:** 4
**Target table:** stg_customers

### Schema

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| customer_id | integer | no | Primary key |
| name | string | no | |
| email | string | yes | 2% null |
| tier | string | no | Enum: [gold, silver, bronze] |

### Cleaning Required

- Strip whitespace from name and email
- Lowercase email

### Verified Assertions

- Unique: customer_id (verified: 1200 unique of 1200 total)
- Accepted values: tier in [gold, silver, bronze] (100% match)

## Relationships

| From | To | Type | Match Rate | Orphans |
|------|-----|------|-----------|---------|
| Orders.customer_id | Customers.customer_id | FK | 100% | 0 |
| Orders.product_id | Products.product_id | FK | 99.8% | 3 |

## Assumptions

- Orders.total rounding: 5 rows differ from quantity * unit_price by <$0.01 — assumed rounding
- Products with no orders: 15 products have zero order references — assumed inactive
```
