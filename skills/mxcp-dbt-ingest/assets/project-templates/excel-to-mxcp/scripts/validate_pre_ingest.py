#!/usr/bin/env python3
"""
Pre-ingestion validator — checks Excel structure against project manifest.

Usage:
    python scripts/validate_pre_ingest.py <excel_file> [--manifest project-manifest.md]

Checks:
1. Sheet presence (missing/new)
2. Column presence with normalized name matching + fuzzy rename detection
3. Column type comparison against manifest
4. Row count change detection (configurable threshold)

Exit codes:
    0 = structure matches expectations
    1 = structural changes detected (review needed)
    2 = critical error (file missing, unreadable)
"""

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

# Import shared utilities from canonical module
sys.path.insert(0, str(Path(__file__).parent))
from canonical import normalize_column_name as normalize_col, levenshtein
from profile_excel import detect_header_row


def infer_column_type(series: pd.Series) -> str:
    """Quick type inference for comparison against manifest."""
    non_null = series.dropna()
    if len(non_null) == 0:
        return "empty"
    numeric = pd.to_numeric(non_null, errors="coerce")
    if numeric.notna().mean() > 0.9:
        clean = numeric.dropna()
        try:
            if (clean == clean.round(0)).all() and clean.abs().max() < 2**53:
                return "integer"
        except (OverflowError, ValueError):
            pass
        return "number"
    try:
        dates = pd.to_datetime(non_null, errors="coerce", format="mixed")
        if dates.notna().mean() > 0.95:
            return "datetime"
    except Exception:
        pass
    return "string"


def parse_manifest(manifest_path: Path) -> dict:
    """Extract expected schema from project-manifest.md."""
    if not manifest_path.exists():
        return {}

    content = manifest_path.read_text()
    manifest = {"sheets": {}}

    current_sheet = None
    in_columns = False

    for line in content.split("\n"):
        sheet_match = re.match(r"^## Sheet: (.+)", line)
        if sheet_match:
            current_sheet = sheet_match.group(1).strip()
            manifest["sheets"][current_sheet] = {"columns": [], "row_count": None}
            in_columns = False
            continue

        if current_sheet:
            row_match = re.match(r"\*\*Rows:\*\*\s*(\d+)", line)
            if row_match:
                manifest["sheets"][current_sheet]["row_count"] = int(row_match.group(1))

            if "| Column |" in line:
                in_columns = True
                continue
            if in_columns and line.startswith("|---"):
                continue
            if in_columns and line.startswith("| "):
                parts = [p.strip() for p in line.split("|")[1:-1]]
                if len(parts) >= 2:
                    manifest["sheets"][current_sheet]["columns"].append({
                        "name": parts[0],
                        "type": parts[1] if len(parts) > 1 else "unknown",
                    })
            elif in_columns and not line.startswith("|"):
                in_columns = False

    return manifest


def validate(excel_path: Path, manifest: dict, row_count_threshold: float = 0.20) -> list:
    """Validate Excel structure against manifest. Returns list of issues."""
    issues = []

    try:
        excel_file = pd.ExcelFile(excel_path)
    except Exception as e:
        return [{"severity": "CRITICAL", "message": f"Cannot read Excel file: {e}"}]

    current_sheets = set(excel_file.sheet_names)
    expected_sheets = set(manifest.get("sheets", {}).keys())

    missing = expected_sheets - current_sheets
    new = current_sheets - expected_sheets

    for s in missing:
        issues.append({"severity": "CRITICAL", "message": f"Sheet '{s}' is missing from Excel file"})
    for s in new:
        issues.append({"severity": "WARNING", "message": f"New sheet '{s}' found in Excel file (not in manifest)"})

    for sheet_name, expected in manifest.get("sheets", {}).items():
        if sheet_name not in current_sheets:
            continue

        # Use profiler's header detection for consistent reading
        header_row = detect_header_row(excel_path, sheet_name)
        df = pd.read_excel(excel_path, sheet_name=sheet_name, header=header_row)
        # Flatten multi-level columns if multi-row header was detected
        if isinstance(header_row, list) and isinstance(df.columns, pd.MultiIndex):
            df.columns = ['_'.join(str(c) for c in col if str(c) != '').strip('_')
                          for col in df.columns.values]
        df = df.dropna(how="all").dropna(axis=1, how="all")

        # --- Column name comparison with normalization ---
        actual_raw = {str(c): normalize_col(str(c)) for c in df.columns}
        expected_raw = {c["name"]: normalize_col(c["name"]) for c in expected.get("columns", [])}

        actual_norm = set(actual_raw.values())
        expected_norm = set(expected_raw.values())

        missing_norm = expected_norm - actual_norm
        new_norm = actual_norm - expected_norm

        # Fuzzy rename detection: pair missing + new columns with small edit distance
        renames_found = set()
        for m_norm in list(missing_norm):
            m_orig = next(k for k, v in expected_raw.items() if v == m_norm)
            best_match = None
            best_dist = float('inf')
            for n_norm in list(new_norm):
                dist = levenshtein(m_norm, n_norm)
                if dist < best_dist and dist <= max(3, len(m_norm) * 0.3):
                    best_dist = dist
                    best_match = n_norm
            if best_match:
                n_orig = next(k for k, v in actual_raw.items() if v == best_match)
                issues.append({
                    "severity": "WARNING",
                    "message": f"Sheet '{sheet_name}': column likely RENAMED: '{m_orig}' → '{n_orig}' (edit distance: {best_dist})",
                })
                renames_found.add(m_norm)
                renames_found.add(best_match)
                missing_norm.discard(m_norm)
                new_norm.discard(best_match)

        for m_norm in missing_norm:
            m_orig = next(k for k, v in expected_raw.items() if v == m_norm)
            issues.append({"severity": "CRITICAL", "message": f"Sheet '{sheet_name}': column '{m_orig}' is missing"})
        for n_norm in new_norm:
            n_orig = next(k for k, v in actual_raw.items() if v == n_norm)
            issues.append({"severity": "WARNING", "message": f"Sheet '{sheet_name}': new column '{n_orig}' found"})

        # --- Type comparison for matched columns ---
        expected_types = {normalize_col(c["name"]): c.get("type", "unknown") for c in expected.get("columns", [])}
        for col in df.columns:
            norm = normalize_col(str(col))
            if norm in expected_types and expected_types[norm] != "unknown":
                actual_type = infer_column_type(df[col])
                expected_type = expected_types[norm].split()[0].lower()  # Handle "integer (enum?)" etc.
                if actual_type != expected_type and actual_type != "empty":
                    issues.append({
                        "severity": "WARNING",
                        "message": f"Sheet '{sheet_name}': column '{col}' type changed: expected '{expected_type}', got '{actual_type}'",
                    })

        # --- Row count change detection ---
        if expected.get("row_count"):
            actual_rows = len(df)
            expected_rows = expected["row_count"]
            pct_change = abs(actual_rows - expected_rows) / max(expected_rows, 1)
            if pct_change > row_count_threshold:
                issues.append({
                    "severity": "WARNING",
                    "message": f"Sheet '{sheet_name}': row count changed from {expected_rows} to {actual_rows} ({pct_change*100:.0f}% change, threshold: {row_count_threshold*100:.0f}%)",
                })

    return issues


def main():
    parser = argparse.ArgumentParser(description="Pre-ingestion structural validator")
    parser.add_argument("excel_file", help="Path to Excel file")
    parser.add_argument("--manifest", default="project-manifest.md", help="Path to project manifest")
    parser.add_argument("--row-threshold", type=float, default=0.20, help="Row count change threshold (0.0-1.0, default 0.20)")
    args = parser.parse_args()

    excel_path = Path(args.excel_file)
    manifest_path = Path(args.manifest)

    if not excel_path.exists():
        print(f"CRITICAL: Excel file not found: {excel_path}")
        sys.exit(2)

    if not manifest_path.exists():
        print(f"WARNING: No manifest found at {manifest_path} — skipping structural validation")
        print("This is expected on first run. Run profiling first.")
        sys.exit(0)

    manifest = parse_manifest(manifest_path)
    issues = validate(excel_path, manifest, row_count_threshold=args.row_threshold)

    if not issues:
        print("PASS: Excel structure matches manifest expectations")
        sys.exit(0)

    critical = [i for i in issues if i["severity"] == "CRITICAL"]
    warnings = [i for i in issues if i["severity"] == "WARNING"]

    print(f"\nValidation Results: {len(critical)} critical, {len(warnings)} warnings\n")
    for issue in issues:
        print(f"  [{issue['severity']}] {issue['message']}")

    if critical:
        print(f"\nFAILED: {len(critical)} critical issues must be resolved before ingestion")
        sys.exit(1)
    else:
        print(f"\nPASSED with warnings: review before proceeding")
        sys.exit(0)


if __name__ == "__main__":
    main()
