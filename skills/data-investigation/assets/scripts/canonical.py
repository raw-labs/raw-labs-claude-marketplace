#!/usr/bin/env python3
"""
Canonical value handling — shared utilities for profiler and validators.

All scripts import from this module to ensure consistent behavior for:
- Column name normalization
- Float comparison with tolerance
- Currency/locale number parsing
- NULL/empty-string classification

This is the single source of truth. Do NOT duplicate these functions.
"""

import re
from datetime import datetime, timedelta


# --- Column name normalization ---

def normalize_column_name(name: str) -> str:
    """Normalize column name for comparison: strip, lowercase, replace non-alnum with _."""
    return re.sub(r'[^a-z0-9]', '_', str(name).strip().lower()).strip('_')


# --- Numeric parsing ---

def strip_currency_pct(value: str) -> str:
    """Strip common currency symbols and percentage signs for numeric parsing."""
    if not isinstance(value, str):
        return value
    cleaned = re.sub(r'[$€£¥₹]', '', value).strip()
    cleaned = re.sub(r'%$', '', cleaned).strip()
    return cleaned


def try_european_decimal(value: str) -> float | None:
    """Try parsing European decimal format: 1.234,56 -> 1234.56"""
    if not isinstance(value, str):
        return None
    match = re.match(r'^-?\d{1,3}(\.\d{3})*(,\d+)?$', value.strip())
    if match:
        try:
            return float(value.strip().replace('.', '').replace(',', '.'))
        except ValueError:
            return None
    return None


# --- Float comparison ---

FLOAT_RTOL = 1e-6   # Relative tolerance
FLOAT_ATOL = 1e-9   # Absolute tolerance


def values_close(source, target, rtol=FLOAT_RTOL, atol=FLOAT_ATOL) -> bool:
    """Compare values with floating-point tolerance.

    Handles None, numeric, and string values gracefully.
    """
    if source is None and target is None:
        return True
    if source is None or target is None:
        return False
    try:
        return abs(float(source) - float(target)) <= atol + rtol * abs(float(target))
    except (TypeError, ValueError):
        return str(source).strip() == str(target).strip()


# --- Date handling ---

def convert_excel_date(value):
    """Convert Excel date serial numbers to datetime.

    openpyxl with data_only=True returns raw serial numbers for dates,
    while pd.read_excel converts them to Timestamps. This function ensures
    consistent date handling when using openpyxl directly.
    """
    if isinstance(value, (int, float)) and 1 < value < 200000:
        try:
            return datetime(1899, 12, 30) + timedelta(days=int(value))
        except (ValueError, OverflowError):
            return value
    return value


# --- Levenshtein distance ---

def levenshtein(s1: str, s2: str) -> int:
    """Simple Levenshtein distance for fuzzy column rename detection."""
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (c1 != c2)))
        prev = curr
    return prev[-1]
