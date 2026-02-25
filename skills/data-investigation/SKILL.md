---
name: data-investigation
description: "This skill should be used when the user asks to 'investigate this Excel file', 'profile this data', 'what is in this spreadsheet', 'analyze this Excel', 'data discovery', or mentions data profiling, Excel investigation, schema detection, or data quality assessment. Provides a self-validating methodology for investigating Excel files before building data pipelines."
---

# Data Investigation

Investigate Excel files to produce a verified `data-model-spec.md` — the contract that drives dbt pipeline generation.

## Investigation Methodology

Follow these 4 steps in order:

### 1. Profile

Run the profiler to get raw structural data:

```bash
# Inside a scaffolded MXCP project:
python scripts/profile_excel.py <excel_file> --output data-profile-report.md

# Standalone investigation (no project yet):
# Copy profiler + canonical.py from skill assets first:
cp <skill-assets>/scripts/profile_excel.py ./profile_excel.py
cp <skill-assets>/scripts/canonical.py ./canonical.py
python profile_excel.py <excel_file> --output data-profile-report.md
```

The profiler script (`assets/scripts/profile_excel.py`, ~800 lines) can be searched with these patterns:
- Header detection: grep `detect_header_row`
- Type inference: grep `infer_column_type`
- FK candidates: grep `find_fk_candidates`
- Merged cells: grep `detect_merged_cells`
- Transposition: grep `detect_transposition`
- Calculated columns: grep `detect_calculated_columns`

The profiler produces `data-profile-report.md` with:
- File metadata (size, MD5, sheet count)
- Per-sheet column profiles (type, nulls, empty strings, unique count, min/max, samples)
- Merged cell regions, hidden sheets, named ranges
- Formula-cell warnings (cells with formulas but no cached values)
- Transposition detection (text first column + numeric/date headers)
- Cross-sheet FK candidates with match rates
- Calculated column detection with mismatch diagnosis
- Mojibake/encoding issue detection
- Multi-row header auto-detection and flattening

### 2. Hypothesize

Read the profile report. For each sheet:
- Identify primary keys (high unique rate, not null)
- Identify foreign keys (cross-sheet FK candidates from profiler)
- Identify calculated columns (formula detection from profiler)
- Identify enums (low cardinality string columns)
- Check domain patterns in `references/domains/` — load the matching domain file as an accelerator

**Domain matching:** Count how many positive indicators from the domain file match columns in the profile. Score: 3+ matches = high confidence, 2 = medium, 1 = low. Check counter-indicators. The domain file provides expected relationships and calculated fields to verify — but STILL test every assertion.

### 3. Test Every Hypothesis

For each detected pattern, run a verification test. Do not skip this step.

**FK verification** — run in pandas or DuckDB:
```python
# Check FK match rate
fk_values = orders_df['customer_id'].dropna().unique()
pk_values = customers_df['customer_id'].dropna().unique()
match_rate = len(set(fk_values) & set(pk_values)) / len(set(fk_values))
# Thresholds: >= 99% VERIFIED, 95-99% WARNING, < 95% POSSIBLE
```

**Calculated column verification:**
```python
import numpy as np
expected = df['quantity'] * df['unit_price']
actual = df['total']
close = np.isclose(actual, expected, rtol=1e-2, atol=1e-6, equal_nan=True)
match_rate = close.mean()
# If match_rate > 0.99 and all diffs < 0.01: rounding
# If match_rate > 0.95 but some large diffs: possible formula error — flag for review
```

**Unique constraint verification:**
```python
unique_rate = df['order_id'].nunique() / len(df)
# 100% = VERIFIED unique, < 100% = NOT unique (check for duplicates)
```

### 4. Report — Write data-model-spec.md

Output follows the format in `references/data-model-spec-format.md`. Every assertion must be tagged:
- **VERIFIED** — tested and confirmed
- **VERIFIED WITH WARNINGS** — mostly confirmed, minor issues noted
- **POSSIBLE** — partial evidence, needs review
- **ASSUMPTION** — unverifiable, pipeline will use unless overridden

## Interpreting Profiler Warnings

| Warning | Action |
|---------|--------|
| Mixed type (column has numbers AND strings) | Check `coercion_failures` — are the non-numeric values headers, totals, or errors? |
| Formula cells with no cached values | File needs to be opened and saved in Excel first |
| Hidden sheets detected | Ask user: include in pipeline or skip? |
| Empty string columns (`empty_string_count > 0`) | Add `NULLIF(TRIM(col), '')` in staging layer |
| Named ranges found | Review — may define data regions, validation lists, or print areas |
| Mojibake/encoding issues | Source file has wrong encoding — re-export from source system with UTF-8 |
| Multi-row headers | Auto-flattened to "Category_Detail" format — verify column names make sense |
| Transposition detected | Data likely needs `pandas.melt()` unpivoting before loading |

## Optional External Skills

If installed, these external skills can assist with visual spot-checks:
- **xlsx skill** (optional): Open the Excel file to visually verify merged cell regions, check formatting, see what the profiler can't capture (colors, conditional formatting)
- **pdf/docx skills** (optional): If the user provides data documentation (data dictionaries, ERD diagrams), read them to inform hypothesis generation

These are not bundled with this plugin — the investigation works fully without them.

## Self-Validation Principles

1. Every structural assertion is tested against the data — never assumed
2. No domain expertise required from the user — the agent tests hypotheses and reports facts
3. Unknowns are flagged as assumptions with clear override instructions
4. Domain patterns are accelerators, not requirements — investigation works without them
5. The output (`data-model-spec.md`) is the single contract between investigation and ingestion
