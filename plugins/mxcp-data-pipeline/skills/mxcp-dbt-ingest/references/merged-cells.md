---
title: "Merged Cell Handling"
description: "Patterns for detecting and handling merged cells in Excel files for dbt ingestion"
---

# Merged Cell Handling

Merged cells are the most common structural challenge in Excel-to-DuckDB pipelines. They cause `NaN` values in pandas because only the top-left cell has a value.

## Detection

The profiler (`profile_excel.py`) reports merged regions per sheet. Check the profile report for entries like:

```
### Merged Cell Regions
| Range | Rows | Cols | Value |
|-------|------|------|-------|
| A1:C1 | 1-1 | 1-3 | Report Title |
| A5:A10 | 5-10 | 1-1 | Category A |
```

## Loading with Merged Cells

Use openpyxl to unmerge and forward-fill before converting to DataFrame:

```python
import openpyxl
import pandas as pd
from datetime import datetime, timedelta


def convert_excel_date(value):
    """Convert Excel date serial numbers to datetime.

    CRITICAL: openpyxl with data_only=True returns raw serial numbers for dates,
    while pd.read_excel converts them to Timestamps. This mismatch is the most
    common cause of silent data corruption in merged-cell Excel files.
    """
    if isinstance(value, (int, float)) and 1 < value < 200000:
        try:
            return datetime(1899, 12, 30) + timedelta(days=int(value))
        except (ValueError, OverflowError):
            return value
    return value


def load_with_merged_cells(filepath, sheet_name):
    """Load an Excel sheet, unmerging cells and forward-filling values."""
    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb[sheet_name]

    # Record merged ranges before unmerging
    merged_ranges = list(ws.merged_cells.ranges)

    # Unmerge all cells and fill with the top-left value
    for merge_range in merged_ranges:
        top_left_value = ws.cell(merge_range.min_row, merge_range.min_col).value
        ws.unmerge_cells(str(merge_range))
        for row in range(merge_range.min_row, merge_range.max_row + 1):
            for col in range(merge_range.min_col, merge_range.max_col + 1):
                ws.cell(row, col, value=top_left_value)

    # Convert to DataFrame
    data = list(ws.values)
    if not data:
        wb.close()
        return pd.DataFrame()
    df = pd.DataFrame(data[1:], columns=data[0])

    # Convert date serial numbers
    for col in df.columns:
        df[col] = df[col].apply(convert_excel_date)

    wb.close()
    return df
```

## dbt Python Model Pattern

```python
# models/staging/stg_categories.py
import pandas as pd
import openpyxl
from datetime import datetime, timedelta


def convert_excel_date(value):
    if isinstance(value, (int, float)) and 1 < value < 200000:
        try:
            return datetime(1899, 12, 30) + timedelta(days=int(value))
        except (ValueError, OverflowError):
            return value
    return value


def model(dbt, session):
    filepath = "source_files/data.xlsx"
    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb["Categories"]

    for merge_range in list(ws.merged_cells.ranges):
        val = ws.cell(merge_range.min_row, merge_range.min_col).value
        ws.unmerge_cells(str(merge_range))
        for r in range(merge_range.min_row, merge_range.max_row + 1):
            for c in range(merge_range.min_col, merge_range.max_col + 1):
                ws.cell(r, c, value=val)

    data = list(ws.values)
    df = pd.DataFrame(data[1:], columns=data[0])
    for col in df.columns:
        df[col] = df[col].apply(convert_excel_date)
    df = df.dropna(how="all")
    wb.close()
    return df
```

## Merged Headers (Multi-level Column Names)

When header rows are merged (e.g., "Q1" spanning Jan/Feb/Mar columns):

```python
def load_merged_headers(filepath, sheet_name, header_rows=[0, 1]):
    """Load sheet with multi-level merged headers."""
    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb[sheet_name]

    # Unmerge header rows
    for merge_range in list(ws.merged_cells.ranges):
        if merge_range.min_row <= max(header_rows) + 1:
            val = ws.cell(merge_range.min_row, merge_range.min_col).value
            ws.unmerge_cells(str(merge_range))
            for r in range(merge_range.min_row, merge_range.max_row + 1):
                for c in range(merge_range.min_col, merge_range.max_col + 1):
                    ws.cell(r, c, value=val)

    data = list(ws.values)
    headers = ['_'.join(str(data[r][c]) for r in header_rows if data[r][c])
               for c in range(len(data[0]))]
    first_data_row = max(header_rows) + 1
    df = pd.DataFrame(data[first_data_row:], columns=headers)
    wb.close()
    return df
```

## Key Reminders

- Always use `data_only=True` when loading with openpyxl for merged cell handling
- Always apply `convert_excel_date()` after openpyxl loading — dates appear as serial numbers
- `pd.read_excel` handles dates automatically but cannot handle merged cells properly
- The profiler detects merged regions — check the profile report before deciding which approach to use
