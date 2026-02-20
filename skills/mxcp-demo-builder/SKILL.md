---
name: mxcp-demo-builder
description: "Build MXCP demo servers for new companies from source data files (Excel, CSV, PDF). Creates a complete GitHub repo with dbt models for data ingestion, MXCP tools for querying, Docker/CI configs, and validates everything passes. Use when asked to 'build an MXCP demo', 'create a demo server', 'onboard a new company to MXCP', or similar. Requires the mxcp-expert skill to be available."
---

# MXCP Demo Builder

Build production-ready MXCP demo servers from raw source data files.

## Prerequisites

- `mxcp-expert` skill available (for MXCP schema knowledge)
- `gh` CLI authenticated (for GitHub repo creation)
- `codex` or `claude` coding agent available
- Python 3 with pandas, openpyxl

## Workflow

### 1. Gather Inputs

Ask for (if not provided):
- **Company name** (used for repo naming: `<company>-mxcp-server`)
- **GitHub org** (default: `raw-labs`)
- **Source data files** (Excel, CSV, PDF — copy to `source_data/`)
- **Data context** (what the data represents, key questions to answer)

### 2. Create Repo & Skeleton

```bash
# Create GitHub repo
gh repo create <org>/<company>-mxcp-server --private --clone
cd <company>-mxcp-server
```

Create these skeleton files (adapt from template below):

**dbt_project.yml:**
```yaml
name: "<company>"
version: "1.0.0"
config-version: 2
profile: "<company>"
model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]
clean-targets: ["target", "dbt_packages"]
```

**profiles.yml:**
```yaml
<company>:
  outputs:
    dev:
      type: duckdb
      path: data/db-default.duckdb
  target: dev
```

**mxcp-config.yml:**
```yaml
mxcp: 1
projects:
  <company>-mxcp-server:
    profiles:
      default: {}
transport:
  http:
    port: 8000
    host: 0.0.0.0
```

**mxcp-site.yml:**
```yaml
mxcp: 1
profile: default
project: <company>
profiles:
  default:
    duckdb:
      path: data/db-default.duckdb
sql_tools:
  enabled: false
dbt:
  enabled: true
  model_paths: ["models"]
  test_paths: ["tests"]
```

**Dockerfile:**
```dockerfile
FROM ghcr.io/raw-labs/mxcp:0.10.0-rc12
COPY --chown=mxcp:mxcp . /mxcp-site/
ENV MXCP_CONFIG=/mxcp-site/mxcp-config.yml
```

Copy `.github/workflows/build-push.yml` and `tests.yml` from `~/workspace/bluesky-nexus-mxcp-server/` and update image name.

Copy `.gitignore` from any existing mxcp-server repo; ensure it includes `data/`, `logs/`, `.venv/`, `target/`.

### 3. Analyze Source Data

Before creating models, inspect the data:

```python
import pandas as pd
# For Excel:
df = pd.read_excel('source_data/file.xlsx', sheet_name=0, header=<row>)
print(f'Shape: {df.shape}')
print(f'Columns: {df.columns.tolist()}')
print(df.head(3).to_dict(orient='records'))
# Check nulls, unique values for key columns
```

Document: row count, key columns, data types, unique categorical values, null counts.

### 4. Create dbt Models

**Pattern:** One Python model per source file under `models/<domain>/`.

```python
import pandas as pd

def model(dbt, session):
    """Load <description> from <source file>."""
    dbt.config(materialized="table")
    
    df = pd.read_excel("source_data/<file>", sheet_name="<sheet>", header=<row>, engine="openpyxl")
    
    # Rename columns to snake_case
    # Convert types: dates, numbers, strings
    # Drop rows missing key fields
    
    return df[final_columns]
```

**Schema:** `models/<domain>/schema.yml` with `not_null` and `accepted_values` tests on key columns.

### 5. Create MXCP Tools

**Pattern:** SQL tools under `tools/<domain>/` querying dbt tables.

Every project should have at minimum:
- **Summary tool** (aggregated overview, no params)
- **Filter tools** (by key dimensions like category, location, date)
- **List tools** (distinct values with counts for each dimension)

Tool template:
```yaml
mxcp: 1
tool:
  name: <tool_name>
  description: |
    <Clear description of what this returns and when to use it.>
  parameters:
    - name: <param>
      type: string
      description: "<description>"
      enum: [<values>]  # if categorical
      examples: [<examples>]
  return:
    type: array
    items:
      type: object
      properties:
        <column>:
          type: <string|number|integer>
  source:
    code: |
      SELECT ... FROM <dbt_table> WHERE ... ORDER BY ...
  tests:
    - name: <test_name>
      description: "<what it checks>"
      arguments:
        - key: <param>
          value: "<value>"
      result_length: <expected_count>
```

### 6. Validate & Test

Run in order:
```bash
mxcp dbt run          # Materialize tables
mxcp validate         # Validate all tool definitions
mxcp test             # Run inline tool tests
mxcp dbt test         # Run dbt schema tests
```

Fix any failures before proceeding.

### 7. Commit & Push

```bash
git add -A
git commit -m "Initial MXCP server for <Company> <domain> analytics"
git push origin main
```

### 8. Deploy (Coolify)

Deployment to https://mxcp.cloud/ is manual via the Coolify dashboard:
1. Add new resource → Docker image
2. Point to `ghcr.io/raw-labs/<company>-mxcp-server:latest`
3. Set port 8000
4. Deploy

## Key Rules

- **All data ingestion happens in dbt Python models** — tools ONLY query DuckDB
- **Never create ingestion tools** — that's an anti-pattern
- **Follow hsbchk-mxcp-server pattern** (simpler than reden)
- **Use the mxcp-expert skill** for schema details and validation rules
- **Test counts must match actual data** — verify with queries before hardcoding
- **Tools need inline tests** — at minimum `result_length` or `result_contains_item`
