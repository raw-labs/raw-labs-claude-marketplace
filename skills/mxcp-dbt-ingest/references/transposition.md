---
title: "Transposition Handling"
description: "Patterns for detecting and handling transposed tables in Excel files"
---

# Transposition Handling

Transposed tables have metrics as rows and time periods (or categories) as columns. They need to be unpivoted before loading into dbt.

## Detection

The profiler detects transposition when:
- First column is text (metric names)
- Other columns are numeric
- Column headers look like dates or time periods (Q1, Jan, 2024, etc.)

Profile report shows:
```
### Transposition Detected
**Reason:** text first column + numeric data + date-like headers
**Suggestion:** Unpivot: use pandas.melt() with first column as id_vars
```

## Unpivoting with pandas.melt()

The most common pattern — convert wide format to long:

```python
import pandas as pd

# Before (transposed):
# | Metric    | Jan  | Feb  | Mar  |
# |-----------|------|------|------|
# | Revenue   | 1000 | 1200 | 1100 |
# | Expenses  | 800  | 900  | 850  |

df = pd.read_excel("source_files/data.xlsx", sheet_name="Monthly")

# Unpivot: first column becomes id, rest become value rows
df_long = pd.melt(
    df,
    id_vars=[df.columns[0]],          # Keep "Metric" as identifier
    var_name="period",                  # Column headers become values in "period"
    value_name="amount"                 # Cell values go into "amount"
)

# After (normalized):
# | Metric   | period | amount |
# |----------|--------|--------|
# | Revenue  | Jan    | 1000   |
# | Revenue  | Feb    | 1200   |
# | Expenses | Jan    | 800    |
```

## dbt Python Model Pattern

```python
# models/staging/stg_monthly_metrics.py
import pandas as pd

def model(dbt, session):
    df = pd.read_excel("source_files/data.xlsx", sheet_name="Monthly")
    df = df.dropna(how="all").dropna(axis=1, how="all")

    # Unpivot: first column is metric name, rest are periods
    id_col = df.columns[0]
    df_long = pd.melt(df, id_vars=[id_col], var_name="period", value_name="amount")

    # Normalize column names
    df_long.columns = [c.strip().lower().replace(' ', '_') for c in df_long.columns]

    return df_long
```

## Full Transpose (Flip Rows and Columns)

When the entire table is rotated (rare):

```python
df = pd.read_excel("source_files/data.xlsx", sheet_name="Summary", header=None)
df = df.T  # Transpose
df.columns = df.iloc[0]  # First row becomes headers
df = df[1:]  # Remove header row from data
df = df.reset_index(drop=True)
```

## Multiple ID Columns

When several columns should stay fixed:

```python
# | Region | Product | Q1  | Q2  | Q3  | Q4  |
# Two id columns (Region, Product), four value columns

df_long = pd.melt(
    df,
    id_vars=["Region", "Product"],
    var_name="quarter",
    value_name="sales"
)
```

## Key Reminders

- Always check the profiler's transposition detection first
- `melt()` is the standard approach — converts wide to long
- Multiple id columns are common — check which columns are identifiers vs values
- After unpivoting, the period column often needs parsing (e.g., "Jan 2024" → date)
- Unpivoted tables may need a pivot back in the mart layer for specific analytics views
