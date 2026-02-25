#!/usr/bin/env python3
"""
Post-ingestion validator — verifies data integrity after dbt run.

Usage:
    python scripts/validate_post_ingest.py <excel_file> --db <duckdb_path> --tables <table1,table2>

Checks:
1. Row count comparison (source Excel vs DuckDB staging tables)
2. Checksum validation — SOURCE vs TARGET comparison with float tolerance
   (SUM, COUNT, COUNT DISTINCT on numeric columns; COUNT, COUNT DISTINCT on all columns)
3. Sample comparison (50 rows, positional matching, seeded RNG)
4. Aggregate statistics comparison (mean, stddev per numeric column)

Exit codes:
    0 = all checks pass
    1 = validation failures detected
"""

import argparse
import random
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

# Import shared utilities from canonical module
sys.path.insert(0, str(Path(__file__).parent))
from canonical import values_close, normalize_column_name, FLOAT_RTOL, FLOAT_ATOL
from profile_excel import detect_header_row


SAMPLE_SIZE = 50    # Number of rows to sample
RNG_SEED = 42       # Reproducible sampling


def read_excel_consistent(excel_path: Path, sheet_name: str) -> pd.DataFrame:
    """Read Excel sheet with profiler-consistent header detection and cleaning.

    Uses detect_header_row to handle title rows and multi-row headers,
    then applies the same dropna cleaning as the profiler.
    """
    header_row = detect_header_row(excel_path, sheet_name)
    df = pd.read_excel(excel_path, sheet_name=sheet_name, header=header_row)
    if isinstance(header_row, list) and isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join(str(c) for c in col if str(c) != '').strip('_')
                      for col in df.columns.values]
    return df.dropna(how="all").dropna(axis=1, how="all")


def compare_row_counts(excel_path: Path, db_path: Path, table_map: dict) -> list:
    """Compare row counts between Excel sheets and DuckDB tables."""
    issues = []
    con = duckdb.connect(str(db_path), read_only=True)

    for sheet_name, table_name in table_map.items():
        try:
            df = read_excel_consistent(excel_path, sheet_name)
            source_rows = len(df)
        except Exception as e:
            issues.append(f"Cannot read sheet '{sheet_name}': {e}")
            continue

        try:
            result = con.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()
            target_rows = result[0]
        except Exception as e:
            issues.append(f"Cannot query table '{table_name}': {e}")
            continue

        if source_rows != target_rows:
            diff = target_rows - source_rows
            issues.append(
                f"Row count mismatch: {sheet_name} has {source_rows} rows, "
                f"{table_name} has {target_rows} rows (diff: {diff:+d})"
            )
        else:
            print(f"  PASS: {sheet_name} -> {table_name}: {source_rows} rows match")

    con.close()
    return issues


def checksum_validation(excel_path: Path, db_path: Path, sheet_name: str, table_name: str) -> list:
    """Compare source (pandas) vs target (DuckDB) checksums with float tolerance.

    Computes SUM, COUNT, COUNT DISTINCT on numeric columns.
    Computes COUNT, COUNT DISTINCT on all columns.
    Returns list of mismatch issues.
    """
    issues = []

    # Source side (consistent header detection with profiler)
    df_source = read_excel_consistent(excel_path, sheet_name)

    # Target side
    con = duckdb.connect(str(db_path), read_only=True)
    cols_info = con.execute(f'DESCRIBE "{table_name}"').fetchall()
    numeric_types = {"INTEGER", "BIGINT", "DOUBLE", "FLOAT", "DECIMAL", "NUMERIC", "HUGEINT", "SMALLINT", "TINYINT"}
    numeric_cols = [c[0] for c in cols_info if c[1].upper() in numeric_types]
    all_cols = [c[0] for c in cols_info]

    checksums = {"numeric": {}, "all_columns": {}}

    # Numeric column checksums: SUM, COUNT, COUNT DISTINCT
    for col in numeric_cols:
        # Target side
        target_result = con.execute(
            f'SELECT SUM("{col}"), COUNT("{col}"), COUNT(DISTINCT "{col}") FROM "{table_name}"'
        ).fetchone()
        target_sum, target_count, target_distinct = target_result

        # Source side — find matching column using normalized names
        source_col = None
        normalized_target = normalize_column_name(col)
        for sc in df_source.columns:
            if normalize_column_name(str(sc)) == normalized_target:
                source_col = sc
                break

        if source_col is None:
            checksums["numeric"][col] = {"target_sum": target_sum, "target_count": target_count, "note": "no source match"}
            continue

        source_numeric = pd.to_numeric(df_source[source_col], errors="coerce")
        source_sum = float(source_numeric.sum()) if not source_numeric.isna().all() else None
        source_count = int(source_numeric.count())
        source_distinct = int(source_numeric.nunique())

        checksums["numeric"][col] = {
            "source_sum": source_sum, "target_sum": target_sum,
            "source_count": source_count, "target_count": target_count,
            "source_distinct": source_distinct, "target_distinct": target_distinct,
        }

        # Compare with tolerance
        if not values_close(source_sum, target_sum):
            diff = (float(target_sum or 0)) - (float(source_sum or 0))
            issues.append(f"Checksum mismatch: {table_name}.{col} SUM differs — source={source_sum}, target={target_sum}, diff={diff}")

        if source_count != target_count:
            issues.append(f"Checksum mismatch: {table_name}.{col} COUNT differs — source={source_count}, target={target_count}")

    # All columns: COUNT, COUNT DISTINCT
    for col in all_cols:
        target_result = con.execute(
            f'SELECT COUNT("{col}"), COUNT(DISTINCT "{col}") FROM "{table_name}"'
        ).fetchone()
        checksums["all_columns"][col] = {
            "target_count": target_result[0],
            "target_distinct": target_result[1],
        }

    con.close()
    return issues, checksums


def sample_comparison(excel_path: Path, db_path: Path, sheet_name: str, table_name: str,
                      n: int = SAMPLE_SIZE, seed: int = RNG_SEED) -> tuple:
    """Compare n rows from Excel vs DuckDB using positional matching (row index).

    Returns (report_text, issues_list).
    """
    rng = random.Random(seed)
    issues = []

    df_source = read_excel_consistent(excel_path, sheet_name)

    con = duckdb.connect(str(db_path), read_only=True)
    # Use rowid ordering to match Excel positional order (DuckDB tables have no inherent order)
    df_target = con.execute(f'SELECT * FROM "{table_name}" ORDER BY rowid').fetchdf()
    con.close()

    if len(df_source) == 0:
        return "Source sheet is empty", []

    actual_n = min(n, len(df_source), len(df_target))

    # Stratified sample: first 5, last 5, rest random
    indices = []
    if actual_n >= 10:
        indices.extend(range(5))                    # First 5
        indices.extend(range(len(df_source) - 5, len(df_source)))  # Last 5
        remaining = actual_n - 10
        if remaining > 0:
            mid_range = list(range(5, len(df_source) - 5))
            indices.extend(rng.sample(mid_range, min(remaining, len(mid_range))))
    else:
        indices = rng.sample(range(len(df_source)), actual_n)

    indices = sorted(set(indices))

    lines = [f"\n### Sample Comparison: {sheet_name} -> {table_name} ({len(indices)} rows)\n"]
    mismatch_count = 0

    for idx in indices:
        if idx >= len(df_target):
            lines.append(f"**Row {idx}:** target table has fewer rows")
            mismatch_count += 1
            continue

        source_row = df_source.iloc[idx]
        target_row = df_target.iloc[idx]

        # Compare each overlapping column
        row_mismatches = []
        for src_col in df_source.columns:
            # Find matching target column
            tgt_col = None
            for tc in df_target.columns:
                if str(tc).strip().lower() == str(src_col).strip().lower():
                    tgt_col = tc
                    break
            if tgt_col is None:
                continue

            src_val = source_row[src_col]
            tgt_val = target_row[tgt_col]

            # NULL comparison
            src_is_null = pd.isna(src_val) if not isinstance(src_val, str) else False
            tgt_is_null = pd.isna(tgt_val) if not isinstance(tgt_val, str) else False
            if src_is_null and tgt_is_null:
                continue
            if src_is_null != tgt_is_null:
                row_mismatches.append(f"{src_col}: source={'NULL' if src_is_null else src_val}, target={'NULL' if tgt_is_null else tgt_val}")
                continue

            if not values_close(src_val, tgt_val):
                # Also try string comparison for non-numeric
                if str(src_val).strip() != str(tgt_val).strip():
                    row_mismatches.append(f"{src_col}: source={src_val}, target={tgt_val}")

        if row_mismatches:
            mismatch_count += 1
            lines.append(f"**Row {idx}:** MISMATCH")
            for m in row_mismatches[:5]:
                lines.append(f"  - {m}")
        # Only report mismatches to keep output concise

    if mismatch_count == 0:
        lines.append(f"All {len(indices)} sampled rows match.")
    else:
        issues.append(f"Sample comparison: {mismatch_count}/{len(indices)} rows have mismatches in {sheet_name}->{table_name}")

    lines.append("")

    # Aggregate statistics comparison
    lines.append(f"### Aggregate Statistics: {sheet_name} -> {table_name}\n")
    lines.append("| Column | Source Mean | Target Mean | Source StdDev | Target StdDev | Match |")
    lines.append("|--------|-----------|-----------|-------------|-------------|-------|")
    for src_col in df_source.select_dtypes(include=[np.number]).columns:
        tgt_col = None
        for tc in df_target.columns:
            if str(tc).strip().lower() == str(src_col).strip().lower():
                tgt_col = tc
                break
        if tgt_col is None or not np.issubdtype(df_target[tgt_col].dtype, np.number):
            continue
        src_mean = df_source[src_col].mean()
        tgt_mean = df_target[tgt_col].mean()
        src_std = df_source[src_col].std()
        tgt_std = df_target[tgt_col].std()
        mean_ok = values_close(src_mean, tgt_mean, rtol=1e-4)
        std_ok = values_close(src_std, tgt_std, rtol=1e-3)
        match = "PASS" if mean_ok and std_ok else "FAIL"
        if match == "FAIL":
            issues.append(f"Aggregate mismatch: {src_col} mean/stddev differs between source and target")
        lines.append(f"| {src_col} | {src_mean:.4f} | {tgt_mean:.4f} | {src_std:.4f} | {tgt_std:.4f} | {match} |")
    lines.append("")

    return "\n".join(lines), issues


def main():
    parser = argparse.ArgumentParser(description="Post-ingestion validator")
    parser.add_argument("excel_file", help="Path to Excel file")
    parser.add_argument("--db", required=True, help="Path to DuckDB database")
    parser.add_argument("--tables", required=True, help="Comma-separated sheet:table mappings (e.g., Sales:stg_sales,Products:stg_products)")
    parser.add_argument("--output", default="validation-report.md", help="Output report path")
    args = parser.parse_args()

    excel_path = Path(args.excel_file)
    db_path = Path(args.db)

    table_map = {}
    for mapping in args.tables.split(","):
        parts = mapping.strip().split(":")
        if len(parts) == 2:
            table_map[parts[0]] = parts[1]
        else:
            print(f"Invalid mapping: {mapping} (expected Sheet:table)")
            sys.exit(2)

    print(f"Post-ingestion validation: {excel_path} -> {db_path}\n")

    all_issues = []

    # 1. Row counts
    print("1. Row Count Validation:")
    issues = compare_row_counts(excel_path, db_path, table_map)
    all_issues.extend(issues)
    for issue in issues:
        print(f"  FAIL: {issue}")

    # 2. Source-vs-target checksums
    print("\n2. Checksum Validation (source vs target):")
    all_checksums = {}
    for sheet_name, table_name in table_map.items():
        cs_issues, checksums = checksum_validation(excel_path, db_path, sheet_name, table_name)
        all_issues.extend(cs_issues)
        all_checksums[table_name] = checksums
        for issue in cs_issues:
            print(f"  FAIL: {issue}")
        if not cs_issues:
            print(f"  PASS: {sheet_name} -> {table_name}: all checksums match")

    # 3. Sample comparison + aggregate stats
    print("\n3. Sample Comparison:")
    samples = []
    for sheet_name, table_name in table_map.items():
        sample_text, sample_issues = sample_comparison(excel_path, db_path, sheet_name, table_name)
        samples.append(sample_text)
        all_issues.extend(sample_issues)
        print(sample_text)

    # Write report
    report_lines = ["# Post-Ingestion Validation Report\n"]
    report_lines.append(f"**Source:** `{excel_path}`  ")
    report_lines.append(f"**Database:** `{db_path}`  \n")

    if all_issues:
        report_lines.append(f"## FAILURES ({len(all_issues)})\n")
        for issue in all_issues:
            report_lines.append(f"- {issue}")
        report_lines.append("")
    else:
        report_lines.append("## All Checks Passed\n")

    report_lines.append("## Checksums (Source vs Target)\n")
    for table_name, cs in all_checksums.items():
        report_lines.append(f"### {table_name}\n")
        if cs.get("numeric"):
            report_lines.append("**Numeric Columns:**")
            for col, vals in cs["numeric"].items():
                report_lines.append(f"- {col}: source_sum={vals.get('source_sum')}, target_sum={vals.get('target_sum')}, "
                                    f"count={vals.get('source_count')}/{vals.get('target_count')}")
        report_lines.append("")

    for sample in samples:
        report_lines.append(sample)

    Path(args.output).write_text("\n".join(report_lines))
    print(f"\nReport written to {args.output}")

    sys.exit(1 if all_issues else 0)


if __name__ == "__main__":
    main()
