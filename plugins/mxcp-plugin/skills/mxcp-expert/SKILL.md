---
name: mxcp-expert
description: "This skill should be used when the user asks to \"create an MXCP project\", \"build an MCP server\", \"initialize mxcp\", \"add a tool endpoint\", \"create a resource\", \"configure authentication\", \"validate endpoints\", \"run mxcp validate\", \"mxcp-site.yml\", or mentions MXCP, MCP server development, SQL/Python endpoints, or DuckDB data access. Provides expert guidance for building production MCP servers using MXCP."
---

# MXCP Expert Skill

MXCP is an enterprise framework for building production-ready AI tools with SQL and Python.

## MXCP Mindset

**Internalize these principles before implementing anything:**

1. **MXCP is opinionated** - There's ONE right way to do most things. Avoid inventing patterns.
2. **If it's common, MXCP provides it** - Auth, testing, data access, policies. Check before building.
3. **Schema docs are truth** - When unsure about syntax, read the schema doc. Avoid guessing.
4. **Validate constantly** - Run `mxcp validate` after every file change. Errors compound.
5. **Read before writing** - 2 minutes reading docs saves 20 minutes debugging.

## Pre-Implementation Checklist

Before writing ANY YAML or code:
- [ ] Read [common-mistakes.md](references/common-mistakes.md) - saves 90% of debugging time
- [ ] Read the relevant schema doc ([tool.md](references/schemas/tool.md), [resource.md](references/schemas/resource.md), or [prompt.md](references/schemas/prompt.md))
- [ ] Check if MXCP already provides this feature (see Capabilities table)
- [ ] Know the required fields and valid types

## MXCP Capabilities

| Category | Features | When to Use |
|----------|----------|-------------|
| **Endpoints** | Tools, Resources, Prompts | Tools=actions/queries, Resources=data by URI, Prompts=message templates |
| **Languages** | SQL, Python | SQL=database/simple, Python=complex logic/APIs |
| **Data Access** | DuckDB (local files, HTTP, S3, PostgreSQL, MySQL, SQLite) | Connect to any data source via DuckDB extensions |
| **Data Transform** | dbt (seeds, SQL models, Python models) | Clean, test, materialize static data |
| **Security** | OAuth, CEL policies, audit logs | Authentication + authorization |
| **Quality** | validate, test, lint, evals | Ensure correctness and LLM usability |
| **Deployment** | stdio, streamable-http | Local dev (stdio), production (HTTP) |

## Reference Documentation

| Category | Key References |
|----------|----------------|
| **Getting Started** | [quickstart](references/getting-started/quickstart.md), [hello-world](references/tutorials/hello-world.md) |
| **Endpoints** | [sql-endpoints](references/tutorials/sql-endpoints.md), [python-endpoints](references/tutorials/python-endpoints.md) |
| **Schemas** | [tool](references/schemas/tool.md), [resource](references/schemas/resource.md), [prompt](references/schemas/prompt.md) |
| **Quality** | [testing](references/quality/testing.md), [validation](references/quality/validation.md), [linting](references/quality/linting.md) |
| **Security** | [authentication](references/security/authentication.md), [policies](references/security/policies.md) |
| **Operations** | [configuration](references/operations/configuration.md), [deployment](references/operations/deployment.md) |
| **Reference** | [cli](references/reference/cli.md), [sql](references/reference/sql.md), [python](references/reference/python.md), [type-system](references/concepts/type-system.md) |
| **Integrations** | [dbt](references/integrations/dbt.md), [duckdb](references/integrations/duckdb.md), [excel](references/integrations/excel-integration.md) |

## Quick Reference: What Docs to Read

| When implementing... | Read first |
|---------------------|------------|
| **Any YAML** | [common-mistakes.md](references/common-mistakes.md) |
| Tools, Resources, Prompts | [tool.md](references/schemas/tool.md), [resource.md](references/schemas/resource.md), [prompt.md](references/schemas/prompt.md) |
| Authentication/Authorization | [authentication.md](references/security/authentication.md), [policies.md](references/security/policies.md) |
| Tests | [testing.md](references/quality/testing.md) |
| Data access (files, DBs) | [duckdb.md](references/integrations/duckdb.md) |
| Data transformation | [dbt.md](references/integrations/dbt.md) |
| Python endpoints | [python.md](references/reference/python.md) |
| SQL endpoints | [sql.md](references/reference/sql.md) |
| Concepts/architecture | [endpoints.md](references/concepts/endpoints.md), [project-structure.md](references/concepts/project-structure.md) |
| Examples/patterns | [examples/index.md](references/examples/index.md) |
| Monitoring, drift | [monitoring.md](references/operations/monitoring.md), [drift-detection.md](references/operations/drift-detection.md) |
| Deployment | [deployment.md](references/operations/deployment.md) |
| Claude Desktop integration | [claude-desktop.md](references/integrations/claude-desktop.md) |
| CLI commands | [cli.md](references/reference/cli.md) |
| Common tasks (how-to) | [common-tasks.md](references/reference/common-tasks.md) |

## Implementation Methodology

**Follow this methodology for every MXCP project. Run `mxcp validate` after EVERY file change.**

### Step 0: Project Setup

```bash
mkdir my-project && cd my-project
uv venv && source .venv/bin/activate
uv pip install mxcp
mxcp init --bootstrap
mxcp validate  # Verify setup
```

### Step 1: Task Analysis & Data Ingestion

**Analyze the task first:**
- What is the user trying to accomplish?
- Is data ingestion needed? What format (CSV, Excel, API, database)?
- Is the data properly structured or does it need transformation?
- What questions will users need answered? (Design schema accordingly)

**Decision: Ingest or query directly?**

| Data Characteristic | Approach | Why |
|---------------------|----------|-----|
| **Static/one-time** (loaded once) | Ingest with dbt | Data quality tests, transformations, persistence |
| **Dynamic/changing** (files updated) | DuckDB direct read | Always reads latest data, no sync needed |

**Ingestion approaches (for static data):**

| Scenario | Approach |
|----------|----------|
| Simple CSV, static reference data | `mxcp dbt seed` |
| Excel, complex transformations | dbt Python models |

**Excel/spreadsheet sources → default to dbt Python models.** Unless the user
asks for something else, ingest `.xlsx`/`.xls` into DuckDB with a **dbt Python
model** (`pd.read_excel(...)` → cleaned DataFrame, materialized as a table). This
beats converting to CSV + `dbt seed`: no manual conversion step, and it handles
multiple sheets, dates, and dirty headers in version-controlled, testable code.
See [excel-integration.md](references/integrations/excel-integration.md) for the
full runnable recipe and [dbt.md](references/integrations/dbt.md) for Python-model
mechanics. Do **not** read the spreadsheet live at request time — ingest once, then
serve endpoints from the materialized table.

**Direct read approaches (for dynamic data):**

```sql
-- DuckDB reads files directly - always gets latest data
SELECT * FROM read_csv_auto('data/sales.csv');
SELECT * FROM read_parquet('data/*.parquet');
SELECT * FROM read_json_auto('https://api.example.com/data.json');
```

**Connect to external databases via DuckDB:**
```sql
-- PostgreSQL (requires postgres extension)
ATTACH 'postgresql://user:pass@host:5432/db' AS pg (TYPE postgres);
SELECT * FROM pg.public.users;

-- MySQL (requires mysql extension)
ATTACH 'host=localhost user=root database=mydb' AS mysql (TYPE mysql);
SELECT * FROM mysql.orders;
```
See [duckdb.md](references/integrations/duckdb.md) for S3, HTTP auth, and secret management.

**Test the ingestion — don't trust it blind.** Ingestion is where data silently
goes wrong (dropped rows, bad types, shifted headers). Every dbt-ingested model
must ship with data-quality tests AND a correctness check:
```bash
mxcp dbt run                     # Materialize the model(s)
mxcp dbt test                    # Schema tests in models/schema.yml MUST pass
# Correctness check: confirm the data actually landed as expected
mxcp query "SELECT count(*) AS rows, count(DISTINCT <key>) AS keys FROM <table>"
mxcp query "SELECT * FROM <table> LIMIT 5"   # eyeball types and values
```
Add `not_null`/`unique` on key columns and `accepted_values` on categoricals in
`models/schema.yml`, and assert known totals/row counts against the source. If the
counts or types don't match the spreadsheet, fix the model before building
endpoints. See [dbt.md](references/integrations/dbt.md#data-quality-tests).

### Step 2: Implementation

**Choose endpoint type based on use case:**

| Use Case | Endpoint Type | Example |
|----------|---------------|---------|
| Query data, perform actions | **Tool** | `get_customer`, `create_order` |
| Access data by URI/path | **Resource** | `employee://{id}/profile` |
| Reusable message templates | **Prompt** | `data_analysis` with Jinja2 |

**Choose implementation language:**

| Scenario | Language | Reference |
|----------|----------|-----------|
| Database queries, aggregations, file reading | SQL | [sql-endpoints.md](references/tutorials/sql-endpoints.md) |
| Complex logic, external APIs, ML, file processing | Python | [python-endpoints.md](references/tutorials/python-endpoints.md) |

**Development cycle for each endpoint:**
```bash
# 1. Create the YAML definition
mxcp validate                    # Fix errors immediately

# 2. Create the implementation (SQL or Python)
mxcp validate                    # Validate again

# 3. Manual verification
mxcp run tool NAME --param key=value

# 4. Add tests and run
mxcp test
```

**Python code requirements:**
- Modular, maintainable code
- Each module independently testable
- Use `pytest` for Python logic testing

### Step 3: Metadata Quality

**Tools will be used by LLMs. Ensure clear metadata:**
- **name**: Descriptive, follows `snake_case`
- **description**: Clear purpose, when to use, what it returns
- **parameters**: Each has description, correct type, examples
- **return**: Documented structure with property descriptions

```yaml
tool:
  name: search_customers
  description: |
    Search customers by name or email. Returns matching customer records
    with contact info and account status. Use for customer lookups.
  parameters:
    - name: query
      type: string
      description: Search term (matches name or email, case-insensitive)
      examples: ["john", "smith@example.com"]
```

### Step 4: Validation

Run after **every** file change:
```bash
mxcp validate
mxcp validate --debug  # For detailed errors
```

### Step 5: Linting

Check metadata quality for LLM consumption:
```bash
mxcp lint
```
Address all warnings about descriptions, examples, and documentation.

### Step 6: Evals (Only if Requested)

Create evals **only if the user explicitly asks**:
```bash
mxcp evals  # AI behavior testing
```

### Step 7: Security & Features (Only if Requested)

Implement **only if the user requests** authentication, policies, or observability:
- **Authentication**: Configure in `~/.mxcp/config.yml` (see Security Features section)
- **Policies**: Add CEL expressions to tool definitions
- **Observability**: Configure OpenTelemetry

**Test security with simulated user context:**
```bash
mxcp run tool NAME --param key=value \
  --user-context '{"role": "admin", "email": "test@example.com"}'
```

### Step 8: Deployment (Only if Requested)

Implement **only if the user explicitly asks** for deployment:

| Transport | Use Case | Command |
|-----------|----------|---------|
| `stdio` | Local dev, Claude Desktop | `mxcp serve` (default) |
| `streamable-http` | Production, web clients | `mxcp serve --transport streamable-http --port 8000` |

See [Deployment](references/operations/deployment.md) for Docker, systemd, production setup.

### Definition of Done

A project is complete when:
- [ ] `mxcp validate` passes with no errors
- [ ] `mxcp test` passes with all tests green
- [ ] `mxcp dbt test` passes (if using dbt)
- [ ] `mxcp lint` shows no critical issues
- [ ] Manual verification with `mxcp run` confirms expected behavior
- [ ] Security tested with `--user-context` (if auth/policies configured)

## Testing Requirements

| Test Type | Must Verify | Reference |
|-----------|-------------|-----------|
| **MXCP endpoint** | Valid inputs, edge cases (nulls, boundaries), error handling | [testing.md](references/quality/testing.md) |
| **dbt data** | `not_null`, `unique`, `relationships`, `accepted_values` | [dbt.md](references/integrations/dbt.md) |
| **Python modules** | Unit tests with `pytest` | - |

## Critical: Use the Default Database

**MXCP automatically creates and manages a DuckDB database.** Do not configure a custom database path unless the user explicitly asks for it.

When you run `mxcp init`, MXCP creates:
- Database at `data/db-default.duckdb` (or `data/db-{profile}.duckdb`)
- All tables, seeds, and dbt models go into this database automatically

**Use the default (no database configuration needed):**
```yaml
# mxcp-site.yml - Minimal config
mxcp: 1
project: my-project
profile: default
# Database is automatically created at data/db-default.duckdb
```

**Only configure `duckdb.path` if the user explicitly requests it** (e.g., shared database, specific location, read-only mode). Do not proactively add database configuration.

## Common Mistakes

**Read [common-mistakes.md](references/common-mistakes.md) before implementing.** It covers YAML syntax errors, type mismatches, Python pitfalls, and SQL gotchas that cause 90% of debugging time. Also read the relevant schema doc ([tool.md](references/schemas/tool.md), [resource.md](references/schemas/resource.md), or [prompt.md](references/schemas/prompt.md)) and run `mxcp validate` after every change.

## Project Structure

```
mxcp-project/                 # `mxcp init` scaffolds all of this
├── mxcp-site.yml       # Project configuration (required)
├── tools/              # Tool definitions (.yml)
├── resources/          # Resource definitions (.yml)
├── prompts/            # Prompt definitions (.yml)
├── sql/                # SQL implementations
├── python/             # Python implementations
├── evals/              # LLM evaluation tests
├── plugins/            # DuckDB/Python plugin definitions
├── drift/              # Drift snapshots (drift-snapshot)
├── audit/              # Audit logs (when enabled)
└── data/               # Database files (db-default.duckdb)
```

**Directory rules:**
- Tools MUST be in `tools/*.yml`
- Resources MUST be in `resources/*.yml`
- Prompts MUST be in `prompts/*.yml`
- SQL files in `sql/`, referenced via relative paths
- Python files in `python/`, referenced via relative paths

## Golden Path: Complete Tool Example

**This shows a complete, correct tool with all required fields and tests:**

```yaml
# tools/get_customer.yml
mxcp: 1
tool:
  name: get_customer
  description: Get customer by ID. Returns customer profile with contact info.
  parameters:
    - name: customer_id
      type: integer
      description: The customer's unique identifier
      examples: [1]
  return:
    type: object
    properties:
      id: {type: integer}
      name: {type: string}
      email: {type: string}
  source:
    file: ../sql/get_customer.sql
  tests:
    - name: existing_customer
      description: Looking up a known ID returns that customer's profile
      arguments: [{key: customer_id, value: 1}]
      result_contains: {id: 1}
    # A `type: object` tool raises "No results returned" (not null) when zero rows
    # match, so verify the not-found case via CLI rather than a YAML `result: null`:
    #   mxcp run tool get_customer --param customer_id=99999  # -> Error: No results returned
```

```sql
-- sql/get_customer.sql
SELECT id, name, email FROM customers WHERE id = $customer_id
```

> **Empty-result behavior (verified):** a tool/resource declaring `return.type: object` (a single record) raises `Error: No results returned` when the query matches zero rows — it does **not** return `null`. To represent "maybe absent," use `return.type: array` (an empty match yields `[]`, testable with `result: []` or `result_length: 0`). Test genuine not-found/error cases with `mxcp run`, not YAML assertions.

**SQL vs Python:** Use SQL for queries/aggregations. Use Python (`language: python`) for complex logic, APIs, ML.

## Security Features

**CRITICAL: Use MXCP built-in security. NEVER write custom authentication code.**

| Feature | Built-in Solution | Reference |
|---------|-------------------|-----------|
| Authentication | OAuth in `~/.mxcp/config.yml` | [authentication.md](references/security/authentication.md) |
| Access Control | CEL policies in YAML | [policies.md](references/security/policies.md) |
| User Context | SQL: `get_username()`, `get_user_email()` | [sql.md](references/reference/sql.md) |
| External APIs | SQL: `get_user_external_token()` | [authentication.md](references/security/authentication.md) |
| Audit Logs | Built-in logging | [auditing.md](references/security/auditing.md) |

**Supported OAuth providers:** GitHub, Google, Atlassian, Salesforce, Keycloak

## CLI Quick Reference

```bash
# Project
mxcp init --bootstrap        # Create new project
mxcp list                    # List all endpoints

# Quality
mxcp validate                # Check structure
mxcp test                    # Run tests
mxcp lint                    # Check metadata
mxcp evals                   # AI behavior tests

# Running
mxcp serve                   # Start MCP server
mxcp run tool NAME --param k=v   # Run tool manually

# Database
mxcp query "SELECT 1"        # Execute SQL

# Operations
mxcp drift-snapshot          # Create baseline
mxcp drift-check             # Detect changes
mxcp log --since 1h          # Query audit logs
```

## Troubleshooting

```bash
mxcp validate --debug        # Detailed validation errors
mxcp run tool NAME --debug   # Debug tool execution
mxcp list                    # See available endpoints
```

Common issues: YAML syntax, missing required fields, invalid types, file paths.

## Project Templates

Complete runnable examples in `assets/project-templates/`. Copy and run:

```bash
cp -r assets/project-templates/<template> my-project
cd my-project
mxcp validate && mxcp test
```

### Data & Analytics
| Template | Description |
|----------|-------------|
| `covid_owid` | Data workflow with dbt models, seeds, and prompts |
| `earthquakes` | API-style tool with profile configuration |

### Integrations & OAuth
| Template | Description |
|----------|-------------|
| `confluence` | Confluence integration via plugin with SQL tools |
| `google-calendar` | Google Calendar with Python endpoints |
| `jira` | Jira integration with secrets-based auth |
| `jira-oauth` | Jira integration via OAuth plugin |
| `keycloak` | Keycloak OAuth authentication demo |
| `salesforce` | Salesforce with secrets-based auth and Python |
| `salesforce-oauth` | Salesforce with OAuth flow and Python |

### Plugin Development
| Template | Description |
|----------|-------------|
| `plugin` | DuckDB plugin development example |
| `python-demo` | Python endpoint patterns (good starting point) |

See [Configuration](references/operations/configuration.md) for mxcp-site.yml and config.yml options.
