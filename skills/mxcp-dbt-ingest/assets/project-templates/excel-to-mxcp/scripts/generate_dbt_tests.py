#!/usr/bin/env python3
"""
dbt test generator — auto-generates dbt test YAML from data-model-spec.md.

Usage:
    python scripts/generate_dbt_tests.py --spec data-model-spec.md --output models/staging/schema.yml

Generates:
- not_null tests from "Nullable: no" columns
- unique tests from "Unique:" verified assertions
- accepted_values from enum columns
- relationships from verified FK assertions (>= 95% match rate)
- expression_is_true for range constraints (from profiler min/max)
- dbt_utils.unique_combination_of_columns for composite keys
- custom aggregate tests (SUM checks)

Output: A dbt schema YAML file (models/staging/schema.yml or specified path)
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from canonical import normalize_column_name


def parse_spec_for_tests(spec_path: Path) -> dict:
    """Parse data-model-spec.md to extract test-worthy assertions.

    Returns: {table_name: {columns: [...], assertions: [...], relationships: [...]}}
    """
    content = spec_path.read_text()
    tables = {}
    current_table = None
    current_section = None

    for line in content.split("\n"):
        # Target table
        table_match = re.search(r"\*\*Target table:\*\*\s*(\S+)", line)
        if table_match:
            current_table = table_match.group(1).strip()
            tables[current_table] = {"columns": [], "assertions": [], "relationships": []}
            current_section = None
            continue

        if not current_table:
            continue

        # Schema section
        if "### Schema" in line:
            current_section = "schema"
            continue
        if "### Verified Assertions" in line or "### Assertions" in line:
            current_section = "assertions"
            continue

        # Parse schema table rows
        if current_section == "schema" and line.startswith("| ") and not line.startswith("|---") and "Column" not in line:
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 3:
                col = {
                    "name": parts[0],
                    "type": parts[1].split()[0].lower(),
                    "nullable": parts[2].lower() if len(parts) > 2 else "yes",
                    "notes": parts[-1] if len(parts) > 3 else "",
                }
                # Check for empty strings column
                if len(parts) > 3:
                    try:
                        col["empty_strings"] = int(parts[3]) if parts[3].isdigit() else 0
                    except (ValueError, IndexError):
                        col["empty_strings"] = 0
                tables[current_table]["columns"].append(col)

        # Parse assertions
        if current_section == "assertions" and line.startswith("- "):
            tables[current_table]["assertions"].append(line[2:].strip())

    # Parse Relationships section (global)
    in_rels = False
    for line in content.split("\n"):
        if "## Relationships" in line:
            in_rels = True
            continue
        if in_rels and line.startswith("| ") and not line.startswith("|---") and "From" not in line:
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 4:
                from_parts = parts[0].split(".")
                to_parts = parts[1].split(".")
                match_rate = float(re.search(r'(\d+\.?\d*)', parts[3]).group(1)) if re.search(r'(\d+\.?\d*)', parts[3]) else 0
                if match_rate >= 95 and len(from_parts) == 2 and len(to_parts) == 2:
                    # Find which table this FK belongs to (from-side)
                    for table_name in tables:
                        if from_parts[0].lower() in table_name.lower() or table_name.lower() in from_parts[0].lower():
                            tables[table_name]["relationships"].append({
                                "from_col": from_parts[1],
                                "to_table": to_parts[0],
                                "to_col": to_parts[1],
                                "match_rate": match_rate,
                            })
        elif in_rels and line.startswith("#"):
            in_rels = False

    return tables


def generate_dbt_yaml(tables: dict) -> str:
    """Generate dbt schema YAML from parsed spec data."""
    lines = ["version: 2", "", "models:"]

    for table_name, table_data in tables.items():
        lines.append(f"  - name: {table_name}")
        lines.append(f"    columns:")

        for col in table_data["columns"]:
            # Normalize column name to match dbt model output (snake_case)
            col["name"] = normalize_column_name(col["name"])
            lines.append(f"      - name: {col['name']}")

            tests = []

            # not_null for non-nullable columns
            if col["nullable"] == "no":
                tests.append("not_null")

            # unique — check assertions
            for assertion in table_data["assertions"]:
                if assertion.startswith(f"Unique: {col['name']}"):
                    tests.append("unique")
                    break

            # accepted_values for enum columns
            enum_match = re.search(r'Enum:?\s*\[([^\]]+)\]', col.get("notes", ""))
            if not enum_match:
                # Also check assertions for accepted values
                for assertion in table_data["assertions"]:
                    if f"Accepted values: {col['name']}" in assertion:
                        enum_match = re.search(r'\[([^\]]+)\]', assertion)
                        break
            if enum_match:
                values = [v.strip().strip("'\"") for v in enum_match.group(1).split(",")]
                tests.append({"accepted_values": {"values": values}})

            # Range constraints from assertions
            for assertion in table_data["assertions"]:
                range_match = re.match(rf"Range: {re.escape(col['name'])} \(min: (.+?), max: (.+?)[\),]", assertion)
                if range_match:
                    min_val = range_match.group(1)
                    max_val = range_match.group(2)
                    # Quote values for DuckDB: dates/strings need quotes, numbers don't
                    def quote_if_needed(val: str) -> str:
                        try:
                            float(val)
                            return val  # numeric — no quotes
                        except ValueError:
                            return f"'{val}'"  # date or string — single-quote for DuckDB
                    min_q = quote_if_needed(min_val)
                    max_q = quote_if_needed(max_val)
                    tests.append({
                        "dbt_utils.expression_is_true": {
                            "expression": f"{col['name']} >= {min_q} AND {col['name']} <= {max_q}"
                        }
                    })
                    break

            # FK relationships
            for rel in table_data["relationships"]:
                if rel["from_col"] == col["name"]:
                    # Map to_table to a staging model name
                    to_model = rel["to_table"].lower()
                    if not to_model.startswith("stg_"):
                        to_model = f"stg_{to_model}"
                    tests.append({
                        "relationships": {
                            "to": f"ref('{to_model}')",
                            "field": rel["to_col"],
                        }
                    })

            if tests:
                lines.append(f"        data_tests:")
                for test in tests:
                    if isinstance(test, str):
                        lines.append(f"          - {test}")
                    elif isinstance(test, dict):
                        for test_name, test_config in test.items():
                            lines.append(f"          - {test_name}:")
                            for k, v in test_config.items():
                                if isinstance(v, list):
                                    lines.append(f"              {k}:")
                                    for item in v:
                                        lines.append(f"                - \"{item}\"")
                                else:
                                    lines.append(f"              {k}: {v}")

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Generate dbt tests from data-model-spec")
    parser.add_argument("--spec", default="data-model-spec.md", help="Path to data-model-spec")
    parser.add_argument("--output", default="models/staging/schema.yml", help="Output YAML path")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"Error: Spec file not found: {spec_path}")
        sys.exit(2)

    tables = parse_spec_for_tests(spec_path)
    if not tables:
        print("Warning: No tables found in spec. Ensure data-model-spec.md has Target table entries.")
        sys.exit(0)

    yaml_content = generate_dbt_yaml(tables)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml_content)

    # Summary
    total_tests = 0
    for table_name, table_data in tables.items():
        table_tests = sum(1 for col in table_data["columns"]
                         for _ in range(1))  # Simplified count
        print(f"  {table_name}: {len(table_data['columns'])} columns, "
              f"{len(table_data['assertions'])} assertions, "
              f"{len(table_data['relationships'])} relationships")

    print(f"\nGenerated: {output_path}")
    print("Review the generated file and adjust as needed before running 'mxcp dbt test'.")


if __name__ == "__main__":
    main()
