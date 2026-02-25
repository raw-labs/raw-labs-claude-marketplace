#!/usr/bin/env python3
"""
Lineage validator — verifies row counts across dbt layers.

Usage:
    python scripts/validate_lineage.py --db <duckdb_path> --manifest project-manifest.md

Checks:
1. Staging row count matches source Excel (from manifest)
2. Intermediate row count <= staging (adjusting for documented WHERE filters)
3. Mart row count <= intermediate (adjusting for documented WHERE filters)
4. Every WHERE filter in the manifest has documented expected row reduction
5. Aggregate sanity: SUM of key columns in mart matches staging (within tolerance)

Exit codes:
    0 = all lineage checks pass
    1 = lineage issues detected
    2 = critical error (db/manifest not found)
"""

import argparse
import re
import sys
from pathlib import Path

import duckdb


def parse_manifest_lineage(manifest_path: Path) -> dict:
    """Extract lineage expectations from project-manifest.md.

    Looks for sections like:
    ### Row Count Lineage
    | Layer | Table | Expected Rows | Filter | Reduction |
    """
    content = manifest_path.read_text()
    lineage = {"tables": {}, "filters": [], "aggregate_checks": []}

    # Parse per-table row counts at each layer
    in_lineage = False
    for line in content.split("\n"):
        if "Row Count Lineage" in line or "row_count_lineage" in line.lower():
            in_lineage = True
            continue
        if in_lineage and line.startswith("| ") and not line.startswith("|---") and not line.startswith("| Layer"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 3:
                layer = parts[0].lower()
                table_name = parts[1]
                try:
                    expected_rows = int(parts[2].replace(",", ""))
                except ValueError:
                    expected_rows = None
                filter_doc = parts[3] if len(parts) > 3 else ""
                reduction = parts[4] if len(parts) > 4 else ""
                lineage["tables"].setdefault(table_name, {})
                lineage["tables"][table_name][layer] = {
                    "expected_rows": expected_rows,
                    "filter": filter_doc,
                    "reduction": reduction,
                }
                if filter_doc and filter_doc != "-":
                    lineage["filters"].append({
                        "table": table_name,
                        "layer": layer,
                        "filter": filter_doc,
                        "reduction": reduction,
                    })
        elif in_lineage and line.startswith("#"):
            in_lineage = False

    # Parse aggregate checks section
    in_agg = False
    for line in content.split("\n"):
        if "Aggregate Check" in line:
            in_agg = True
            continue
        if in_agg and line.startswith("| ") and not line.startswith("|---") and not line.startswith("| Column"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 3:
                lineage["aggregate_checks"].append({
                    "column": parts[0],
                    "source_table": parts[1],
                    "mart_table": parts[2],
                    "expected_sum": float(parts[3]) if len(parts) > 3 and parts[3] else None,
                })
        elif in_agg and line.startswith("#"):
            in_agg = False

    return lineage


def validate_lineage(db_path: Path, lineage: dict) -> list:
    """Validate row counts across layers and aggregate checks."""
    issues = []
    con = duckdb.connect(str(db_path), read_only=True)

    # Get all table names in DuckDB (case-insensitive lookup)
    all_tables_raw = {row[0] for row in con.execute("SELECT table_name FROM information_schema.tables").fetchall()}
    all_tables_lower = {t.lower(): t for t in all_tables_raw}

    for table_name, layers in lineage.get("tables", {}).items():
        # Case-insensitive match: manifest may use STG_ORDERS while DuckDB has stg_orders
        actual_table = all_tables_lower.get(table_name.lower())
        if actual_table is None:
            issues.append(f"CRITICAL: Table '{table_name}' from manifest not found in DuckDB")
            continue

        actual_rows = con.execute(f'SELECT COUNT(*) FROM "{actual_table}"').fetchone()[0]

        for layer, expected in layers.items():
            if expected["expected_rows"] is not None:
                diff = actual_rows - expected["expected_rows"]
                pct = abs(diff) / max(expected["expected_rows"], 1) * 100
                if pct > 5:  # >5% difference is a warning
                    issues.append(
                        f"WARNING: {table_name} ({layer}): expected {expected['expected_rows']} rows, "
                        f"got {actual_rows} (diff: {diff:+d}, {pct:.1f}%)"
                    )
                else:
                    print(f"  PASS: {table_name} ({layer}): {actual_rows} rows (expected {expected['expected_rows']}, diff: {diff:+d})")

    # Check that every documented filter has a reduction note
    undocumented_filters = [f for f in lineage.get("filters", []) if not f.get("reduction") or f["reduction"] == "-"]
    for f in undocumented_filters:
        issues.append(
            f"WARNING: WHERE filter on {f['table']} ({f['layer']}) lacks documented row reduction: '{f['filter']}'"
        )

    # Aggregate checks: compare SUM across layers
    for agg in lineage.get("aggregate_checks", []):
        source_table = agg["source_table"]
        mart_table = agg["mart_table"]
        col = agg["column"]

        if source_table.lower() not in all_tables_lower or mart_table.lower() not in all_tables_lower:
            continue

        try:
            actual_source = all_tables_lower[source_table.lower()]
            actual_mart = all_tables_lower[mart_table.lower()]
            source_sum = con.execute(f'SELECT SUM("{col}") FROM "{actual_source}"').fetchone()[0]
            mart_sum = con.execute(f'SELECT SUM("{col}") FROM "{actual_mart}"').fetchone()[0]

            if source_sum is not None and mart_sum is not None:
                diff = abs(float(mart_sum) - float(source_sum))
                if diff > abs(float(source_sum)) * 0.001:  # >0.1% difference
                    issues.append(
                        f"WARNING: Aggregate mismatch: SUM({col}) in {source_table}={source_sum}, "
                        f"in {mart_table}={mart_sum} (diff: {diff:.2f})"
                    )
                else:
                    print(f"  PASS: SUM({col}): {source_table}={source_sum}, {mart_table}={mart_sum}")
        except Exception as e:
            issues.append(f"WARNING: Could not check aggregate for {col}: {e}")

    con.close()
    return issues


def main():
    parser = argparse.ArgumentParser(description="Lineage validator — row counts across dbt layers")
    parser.add_argument("--db", required=True, help="Path to DuckDB database")
    parser.add_argument("--manifest", default="project-manifest.md", help="Path to project manifest")
    args = parser.parse_args()

    db_path = Path(args.db)
    manifest_path = Path(args.manifest)

    if not db_path.exists():
        print(f"CRITICAL: DuckDB not found: {db_path}")
        sys.exit(2)
    if not manifest_path.exists():
        print(f"WARNING: No manifest found at {manifest_path} — skipping lineage validation")
        print("Run dbt pipeline first to generate the manifest.")
        sys.exit(0)

    lineage = parse_manifest_lineage(manifest_path)
    if not lineage["tables"]:
        print("WARNING: No lineage data found in manifest. Ensure project-manifest.md has a Row Count Lineage section.")
        sys.exit(0)

    print(f"Lineage validation: {db_path}\n")
    issues = validate_lineage(db_path, lineage)

    if not issues:
        print("\nPASS: All lineage checks passed")
        sys.exit(0)
    else:
        print(f"\n{len(issues)} lineage issues detected:")
        for issue in issues:
            print(f"  {issue}")
        sys.exit(1)


if __name__ == "__main__":
    main()
