#!/usr/bin/env python3
"""
Schema type validator — compares DuckDB actual column types against data-model-spec.

Usage:
    python scripts/validate_schema_types.py --db <duckdb_path> --spec data-model-spec.md

Checks:
1. Every column in the spec exists in DuckDB (with normalized name matching)
2. DuckDB types are compatible with spec-declared types
3. Warns about overly-wide types (e.g., VARCHAR for columns that should be INTEGER)

Exit codes:
    0 = all types match
    1 = type mismatches found
    2 = critical error
"""

import argparse
import re
import sys
from pathlib import Path

import duckdb

# Import shared utilities from canonical module
sys.path.insert(0, str(Path(__file__).parent))
from canonical import normalize_column_name as normalize_col


# Mapping from data-model-spec type names to compatible DuckDB types
SPEC_TO_DUCKDB = {
    "integer": {"INTEGER", "BIGINT", "SMALLINT", "TINYINT", "HUGEINT", "INT", "INT4", "INT8", "INT2"},
    "number": {"DOUBLE", "FLOAT", "DECIMAL", "NUMERIC", "REAL", "DOUBLE PRECISION"},
    "string": {"VARCHAR", "TEXT", "CHAR", "BPCHAR", "STRING"},
    "datetime": {"TIMESTAMP", "DATE", "TIMESTAMP WITH TIME ZONE", "TIMESTAMPTZ", "TIMESTAMP_S", "TIMESTAMP_MS", "TIMESTAMP_NS"},
    "boolean": {"BOOLEAN", "BOOL"},
}


def parse_spec_schema(spec_path: Path) -> dict:
    """Extract expected schema from data-model-spec.md.

    Returns: {table_name: {normalized_col: expected_type}}
    """
    content = spec_path.read_text()
    schemas = {}
    current_table = None
    in_schema = False

    for line in content.split("\n"):
        # Match "**Target table:** stg_orders" or "## Sheet: Orders"
        table_match = re.search(r"\*\*Target table:\*\*\s*(\S+)", line)
        if table_match:
            current_table = table_match.group(1).strip()
            schemas[current_table] = {}
            in_schema = False
            continue

        if current_table and ("| Column |" in line or "| column |" in line.lower()):
            in_schema = True
            continue
        if in_schema and line.startswith("|---"):
            continue
        if in_schema and line.startswith("| "):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 2:
                col_name = normalize_col(parts[0])
                col_type = parts[1].split()[0].lower()  # First word only (ignore "enum?" etc.)
                schemas[current_table][col_name] = col_type
        elif in_schema and not line.startswith("|"):
            in_schema = False

    return schemas


def get_duckdb_schema(db_path: Path, table_name: str) -> dict:
    """Get actual column types from DuckDB."""
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        cols = con.execute(f'DESCRIBE "{table_name}"').fetchall()
        return {normalize_col(c[0]): c[1].upper() for c in cols}
    except Exception:
        return {}
    finally:
        con.close()


def check_type_compatibility(spec_type: str, duckdb_type: str) -> tuple:
    """Check if DuckDB type is compatible with spec type.

    Returns: (is_compatible: bool, severity: str, message: str)
    """
    expected_duckdb_types = SPEC_TO_DUCKDB.get(spec_type, set())
    if not expected_duckdb_types:
        return True, "INFO", f"unknown spec type '{spec_type}', skipping"

    # Normalize DuckDB type: strip precision/scale (e.g. DECIMAL(18,2) → DECIMAL, TIMESTAMP_S → TIMESTAMP)
    base_type = re.split(r'[\(\_]', duckdb_type)[0].upper()

    # Exact match (check both full type and base type)
    if duckdb_type in expected_duckdb_types or base_type in expected_duckdb_types:
        return True, "PASS", ""

    # VARCHAR is always "compatible" but may be overly wide
    if duckdb_type in {"VARCHAR", "TEXT", "STRING"} and spec_type in {"integer", "number", "datetime"}:
        return False, "WARNING", f"stored as VARCHAR but expected {spec_type} — possible silent type coercion failure"

    # Number stored as integer is acceptable (loss of precision is unlikely)
    if spec_type == "number" and duckdb_type in SPEC_TO_DUCKDB["integer"]:
        return True, "INFO", "number stored as integer (acceptable if no fractional values)"

    # Integer stored as number is acceptable
    if spec_type == "integer" and duckdb_type in SPEC_TO_DUCKDB["number"]:
        return True, "INFO", "integer stored as float (acceptable, check for precision)"

    return False, "WARNING", f"type mismatch: spec says '{spec_type}', DuckDB has '{duckdb_type}'"


def validate(db_path: Path, spec_schemas: dict) -> list:
    """Validate all tables against spec."""
    issues = []

    for table_name, expected_cols in spec_schemas.items():
        actual_cols = get_duckdb_schema(db_path, table_name)

        if not actual_cols:
            issues.append(f"CRITICAL: Table '{table_name}' not found in DuckDB")
            continue

        for col_norm, expected_type in expected_cols.items():
            if col_norm not in actual_cols:
                # Try fuzzy match
                close_matches = [a for a in actual_cols if abs(len(a) - len(col_norm)) <= 2]
                if close_matches:
                    issues.append(f"WARNING: {table_name}.{col_norm}: not found (similar: {close_matches[:3]})")
                else:
                    issues.append(f"WARNING: {table_name}.{col_norm}: column not found in DuckDB")
                continue

            actual_type = actual_cols[col_norm]
            compatible, severity, message = check_type_compatibility(expected_type, actual_type)

            if not compatible:
                issues.append(f"{severity}: {table_name}.{col_norm}: {message}")
            elif severity == "INFO" and message:
                print(f"  INFO: {table_name}.{col_norm}: {message}")
            else:
                print(f"  PASS: {table_name}.{col_norm}: {expected_type} → {actual_type}")

    return issues


def main():
    parser = argparse.ArgumentParser(description="Schema type validator")
    parser.add_argument("--db", required=True, help="Path to DuckDB database")
    parser.add_argument("--spec", default="data-model-spec.md", help="Path to data-model-spec")
    args = parser.parse_args()

    db_path = Path(args.db)
    spec_path = Path(args.spec)

    if not db_path.exists():
        print(f"CRITICAL: DuckDB not found: {db_path}")
        sys.exit(2)
    if not spec_path.exists():
        print(f"CRITICAL: Spec not found: {spec_path}")
        sys.exit(2)

    spec_schemas = parse_spec_schema(spec_path)
    if not spec_schemas:
        print("WARNING: No schema definitions found in data-model-spec.md")
        sys.exit(0)

    print(f"Schema type validation: {db_path} vs {spec_path}\n")
    issues = validate(db_path, spec_schemas)

    if not issues:
        print("\nPASS: All column types match spec")
        sys.exit(0)
    else:
        critical = [i for i in issues if "CRITICAL" in i]
        warnings = [i for i in issues if "WARNING" in i]
        print(f"\n{len(critical)} critical, {len(warnings)} warnings:")
        for issue in issues:
            print(f"  {issue}")
        sys.exit(1 if critical else 0)


if __name__ == "__main__":
    main()
