---
name: mxcp-expert
description: Expert guidance for building production MCP servers using MXCP (Model Context Protocol eXtension Platform), an enterprise framework with SQL and Python endpoints, security, testing, and deployment. Use when: (1) Creating or initializing MXCP projects or MCP servers, (2) Building MCP tools, resources, or prompts, (3) Configuring endpoints, authentication, or policies, (4) Testing, validating, or debugging MXCP applications, or any task involving MXCP or MCP server development.
---

# MXCP Expert Skill

MXCP (Model Context Protocol eXtension Platform) is an enterprise-grade framework for building production-ready AI tools with SQL and Python.

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

## Core Principles

**This skill prioritizes:**

1. **Use Built-in Features First** - ALWAYS use MXCP's built-in capabilities before writing custom code. If unsure, check the documentation first
2. **Use uv for environments** - Always create venv with `uv venv` and activate before running mxcp
3. **Security First** - Use parameterized queries, validate inputs, implement authentication and policies
4. **Validation Always** - Run `mxcp validate` after every change, fix errors immediately
5. **Test Everything** - Write tests for all endpoints, run `mxcp test` before proceeding
6. **Quality Checks** - Use `mxcp lint` to improve LLM understanding of tools
7. **Incremental Development** - Build one tool at a time, validate before adding the next

**NEVER implement these manually - MXCP provides them. Read the linked docs before implementing:**

| Category | WRONG (custom code) | RIGHT (built-in) | Docs |
|----------|---------------------|------------------|------|
| **Authentication** | API keys, token validation, login endpoints | OAuth in config, `get_username()` in SQL | [authentication.md](references/security/authentication.md) |
| **Authorization** | Python if/else role checks, permission tables | CEL policies in YAML (`user.role`, `user.email`) | [policies.md](references/security/policies.md) |
| **External API auth** | Store/manage tokens, refresh logic | `get_user_external_token()` in SQL | [authentication.md](references/security/authentication.md) |
| **Database setup** | Create DuckDB manually, custom path | Auto-created at `data/db-default.duckdb` | [configuration.md](references/operations/configuration.md) |
| **Data ingestion** | Python scripts to load CSV/Excel | dbt seeds, Python models, DuckDB `read_*` | [dbt.md](references/integrations/dbt.md) |
| **File reading** | Python open/pandas in tools | `read_csv_auto()`, `read_parquet()` | [duckdb.md](references/integrations/duckdb.md) |
| **HTTP requests** | - | SQL: `read_json_auto()` for simple fetches; Python endpoint for complex API logic | [duckdb.md](references/integrations/duckdb.md), [python-endpoints.md](references/tutorials/python-endpoints.md) |
| **Testing** | Custom pytest for endpoints | `mxcp test` with YAML tests | [testing.md](references/quality/testing.md) |
| **Audit logging** | Custom logging code | Built-in `mxcp log` | [auditing.md](references/security/auditing.md) |
| **Configuration** | Custom config files, hardcoded values | Profiles, `${ENV_VARS}` | [configuration.md](references/operations/configuration.md) |

**Environment setup (required before any mxcp command):**
```bash
uv venv && source .venv/bin/activate
uv pip install mxcp
```

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

**After ingestion (if using dbt), verify:**
```bash
mxcp dbt test                    # Data quality tests
mxcp query "SELECT * FROM table LIMIT 5"  # Manual verification
```

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

**These cause validation errors.** See [common-mistakes.md](references/common-mistakes.md) for detailed examples.

| Mistake | Fix |
|---------|-----|
| Missing `tool:` wrapper | Add `tool:` before name/description |
| Missing parameter description | Add `description:` to every parameter |
| `type: int` | Use `type: integer` |
| `type: map` | Use `type: object` |
| `format: datetime` | Use `format: date-time` |
| `name: user-name` | Use `name: user_name` (no hyphens) |
| Both `code:` and `file:` | Use only one |

**Valid types:** `string`, `number`, `integer`, `boolean`, `array`, `object`

## Project Structure

```
mxcp-project/
├── mxcp-site.yml       # Project configuration (required)
├── tools/              # Tool definitions (.yml)
├── resources/          # Resource definitions (.yml)
├── prompts/            # Prompt definitions (.yml)
├── sql/                # SQL implementations
├── python/             # Python implementations
├── evals/              # LLM evaluation tests
└── data/               # Database files (db-default.duckdb)
```

**Directory rules:**
- Tools MUST be in `tools/*.yml`
- Resources MUST be in `resources/*.yml`
- Prompts MUST be in `prompts/*.yml`
- SQL files in `sql/`, referenced via relative paths
- Python files in `python/`, referenced via relative paths

## SQL vs Python Tools

**Use SQL for:**
- Database queries
- Data aggregations
- Simple transformations

**Use Python for:**
- Complex business logic
- External API calls
- ML model inference
- File processing

### SQL Tool Example

```yaml
mxcp: 1
tool:
  name: get_user
  description: Get user by ID
  parameters:
    - name: user_id
      type: integer
      description: User ID
  return:
    type: object
  source:
    code: |
      SELECT id, name, email
      FROM users
      WHERE id = $user_id
```

### Python Tool Example

```yaml
mxcp: 1
tool:
  name: analyze_data
  description: Analyze data with Python
  language: python
  parameters:
    - name: dataset
      type: string
      description: Dataset name
  return:
    type: object
  source:
    file: ../python/analysis.py
```

```python
# python/analysis.py
from mxcp.runtime import db

def analyze_data(dataset: str) -> dict:
    # Use validated table names or query specific tables
    allowed_tables = {"users", "orders", "products"}
    if dataset not in allowed_tables:
        return {"error": f"Unknown dataset: {dataset}"}

    # Table names can't be parameterized - use validated string
    results = db.execute(f"SELECT * FROM {dataset}")
    return {"count": len(results), "data": results}
```

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

Complete runnable examples in `assets/project-templates/`. Start with:
- `python-demo` - Python endpoint patterns
- `covid_owid` - Data workflow with dbt

```bash
cp -r assets/project-templates/python-demo my-project
cd my-project
mxcp validate && mxcp test
```

See [Configuration](references/operations/configuration.md) for mxcp-site.yml and config.yml options.
