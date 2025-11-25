---
name: mxcp-expert
description: This skill must be used with any prompt that uses MXCP. MXCP is an enterprise-grade MCP (Model Context Protocol) framework for building production AI applications with SQL and Python endpoints, security, audit trails, policy enforcement, and comprehensive testing. Use this skill when working with MXCP in any capacity including creating, building, initializing, setting up, or editing MXCP servers or projects, configuring MCP tools/resources/prompts, implementing endpoints, setting up authentication/policies, debugging validation errors, or troubleshooting MXCP applications.
---

# MXCP: Enterprise MCP Framework

MXCP is an enterprise-grade MCP (Model Context Protocol) framework for building production AI applications with SQL and Python. This skill provides comprehensive guidance for working with MXCP projects.

**This skill supports both creating new and editing existing MXCP projects.** Use this skill whether you're starting a new project from scratch or modifying an existing MXCP server (adding/removing tools, updating configurations, changing implementations, fixing validation errors, etc.).

## Scope: Technical Implementation Only

This skill focuses on **how to implement** MCP servers using MXCP, not **what to implement**.

**In Scope**:
- Choosing technical approaches (SQL vs Python, OAuth vs token auth)
- Implementing endpoints, authentication, policies
- Testing, validation, debugging
- Security and robustness patterns

**Out of Scope**:
- Defining business requirements or use cases
- Determining what features the MCP server should provide
- Business logic design decisions

**When user needs are unclear technically**: Ask clarifying questions about data sources, authentication, access patterns.

**When user needs are unclear functionally**: Ask the user to clarify their business requirements before proceeding.

## Quick Reference

**When to use this skill:**
- Creating or initializing new MXCP projects
- Editing existing MXCP projects (adding, removing, or modifying any components)
- Defining or modifying MCP tools, resources, or prompts
- Implementing or updating SQL queries or Python endpoints
- Configuring or changing authentication, policies, or audit logging
- Setting up or modifying dbt integration for data transformation
- Testing, validating, or debugging MXCP endpoints
- Fixing validation errors from `mxcp validate`, `mxcp test`, or `mxcp lint`
- Refactoring or restructuring MXCP project files
- Deploying MXCP servers to production

**New to MXCP? Quick navigation:**
- **First time?** → See [Getting Started](#getting-started) for project initialization
- **Learning by example?** → See [Project Templates](#working-with-project-templates) (14 complete examples)
- **Building Python tools?** → Copy `assets/project-templates/python-demo/`
- **Working with CSV data?** → Copy `assets/project-templates/covid_owid/`
- **Need OAuth integration?** → Copy `assets/project-templates/google-calendar/`
- **Stuck on an error?** → See **references/debugging-guide.md**
- **Need YAML validation?** → Use `python scripts/validate_yaml.py` (see [YAML Schema Validation](#yaml-schema-validation))

## ⚠️ COMMON MISTAKES TO AVOID

**READ THIS BEFORE CREATING ANY TOOLS** - These mistakes cause validation errors:

### 1. Wrong Tool Definition Structure

❌ **WRONG** (Missing `tool:` wrapper):
```yaml
mxcp: 1
name: get_calendar
description: ...
language: python
```

✅ **CORRECT**:
```yaml
mxcp: 1
tool:
  name: get_calendar
  description: ...
  language: python
```

**Fix**: Always add `tool:` as a top-level key after `mxcp: 1`.

### 2. Using `type:` Instead of `language:` for Python Tools

❌ **WRONG**:
```yaml
tool:
  name: my_tool
  type: python  # ❌ Wrong field name
```

✅ **CORRECT**:
```yaml
tool:
  name: my_tool
  language: python  # ✅ Correct for Python tools
```

**Fix**: Use `language: python` for Python tools. Use `type: sql` for SQL tools.

### 3. Misusing the `required:` Field

❌ **WRONG** (Will cause validation error):
```yaml
parameters:
  - name: ticker
    type: string
    required: true  # ❌ Causes: "True is not of type 'array'"
```

❌ **ALSO WRONG**:
```yaml
parameters:
  - name: city
    type: string
    required: false  # ❌ Not valid syntax
```

✅ **CORRECT** (Required parameter):
```yaml
parameters:
  - name: ticker
    type: string
    description: "Stock ticker symbol"
    # No default = required by default
```

✅ **CORRECT** (Optional parameter):
```yaml
parameters:
  - name: city
    type: string
    description: "Filter by city (optional)"
    default: null  # Makes it optional
```

✅ **CORRECT** (Optional with specific default):
```yaml
parameters:
  - name: limit
    type: integer
    description: "Maximum results"
    default: 100  # Optional, defaults to 100
```

**Fix**:
- For required parameters: Don't add `required:` field at all
- For optional parameters: Add `default: null` or `default: <value>`

### 4. Not Validating Early Enough

❌ **WRONG** (Creating multiple tools before validating):
```bash
# Create tool1.yml
# Create tool2.yml
# Create tool3.yml
# Create tool4.yml
mxcp validate  # ❌ Now you have errors in 4 files!
```

✅ **CORRECT** (Validate after EACH tool):
```bash
# Create tool1.yml
mxcp validate  # ✅ Fix errors NOW
# Create tool2.yml
mxcp validate  # ✅ Fix errors NOW
# Continue...
```

**Fix**: Run `mxcp validate` immediately after creating EACH tool definition.

### 5. Not Reading Examples First

❌ **WRONG**: Creating YAML from scratch based on assumptions.

✅ **CORRECT**:
1. Read **references/minimal-working-examples.md** FIRST
2. Copy a working example
3. Modify incrementally
4. Validate after each change

## Before You Start: Mandatory Checklist

**Before creating ANY tool, complete this checklist in order:**

- [ ] 1. Read **references/minimal-working-examples.md** to see working examples
- [ ] 2. Identify which example is closest to the use case
- [ ] 3. Copy the relevant example as a starting point
- [ ] 4. Review the tool template below
- [ ] 5. Modify the copied example incrementally
- [ ] 6. Validate after EACH change

**DO NOT skip this checklist. DO NOT create YAML from scratch.**

## Quick Start: Tool Templates

**Copy ready-to-use templates to avoid syntax errors:**

- **Python Tool Template** - For custom logic, API calls, complex processing
- **SQL Tool Template** - For database queries and data retrieval
- **Resource Template** - For static or dynamic data resources
- **Prompt Template** - For LLM instruction prompts

**See references/tool-templates.md** for complete templates with examples.

**Quick template workflow**:
1. Copy appropriate template from references/tool-templates.md
2. Replace `YOUR_TOOL_NAME` with actual name
3. Update description, parameters, and return types
4. 🛑 **RUN `mxcp validate` IMMEDIATELY** 🛑

## Core Principles

**ALWAYS prioritize in this order:**

1. **Security** - Authentication, authorization, input validation, parameterized queries
2. **Robustness** - Error handling, type validation, data quality checks
3. **Validity** - Structure validation, schema compliance, type safety
4. **Testability** - Test cases, validation scripts, lint checks
5. **Testing** - Run validate/test/lint before deployment
6. **Features** - Implement requested functionality based on user needs

## Mandatory Build Workflow

**CRITICAL: Follow this exact workflow to ensure correctness**

🚨 **DO NOT create multiple tools before validating the first one!** 🚨

### Step-by-Step Process

1. **Create ONE tool definition YAML** (e.g., `tools/my_tool.yml`)
2. 🛑 **STOP! Run `mxcp validate` RIGHT NOW** 🛑
3. **Fix ALL validation errors before proceeding**
4. **Create Python implementation** (if needed, e.g., `python/my_service.py`)
5. 🛑 **STOP! Run `mxcp validate` AGAIN** 🛑
6. **Add tests to the tool YAML** (in `tests:` section)
7. **Run `mxcp test` to verify functionality**
8. **Manual verification**: `mxcp run tool <name>`
9. **Only after ALL checks pass**, create the next tool

### Correct Workflow Example

```bash
# Create first tool
cat > tools/tool1.yml <<EOF
mxcp: 1
tool:
  name: tool1
  ...
EOF

# VALIDATE IMMEDIATELY
mxcp validate  # ← Must pass before continuing!

# Create Python code (if needed)
cat > python/service1.py <<EOF
...
EOF

# VALIDATE AGAIN
mxcp validate  # ← Must pass before continuing!

# Test
mxcp test

# Now create second tool
cat > tools/tool2.yml <<EOF
...
EOF

# VALIDATE IMMEDIATELY
mxcp validate  # ← Always validate after each tool!
```

**Definition of Done**:
- [ ] Virtual environment created with `uv venv`
- [ ] Dependencies installed: `uv pip install mxcp black pyright pytest pytest-asyncio pytest-httpx pytest-cov`
- [ ] `mxcp validate` passes (no errors)
- [ ] `mxcp test` passes (MXCP integration tests)
- [ ] **Python code formatted**: `black python/` passes (if Python code exists)
- [ ] **Type checking passes**: `pyright python/` passes (if Python code exists)
- [ ] `pytest tests/` passes (Python unit tests, if applicable)
- [ ] `dbt test` passes (if using dbt)
- [ ] **Result correctness verified** (tests check actual values)
- [ ] **External calls mocked** (if Python tools use APIs)
- [ ] **Concurrency safe** (Python tools avoid race conditions)
- [ ] **Documentation quality verified** (LLMs can understand with zero context)
- [ ] **Error handling implemented** (Python tools return structured errors)
- [ ] Manual test succeeds with real data
- [ ] Security checklist completed
- [ ] Config.yml provided with instructions

**Two types of tests required**:
1. **MXCP tests** (in YAML `tests:` section) - Integration testing
2. **Python unit tests** (pytest in `tests/` directory) - Isolation testing with mocking

See:
- **references/comprehensive-testing-guide.md** for complete testing strategy
- **references/build-and-validate-workflow.md** for mandatory workflow

**If ANY check fails, the project is NOT done. Fix until all pass.**

## Configuration Policy

**CRITICAL: NEVER edit `~/.mxcp/config.yml`**

**ALWAYS create project-local `config.yml` instead:**

- ✅ **DO**: Create `config.yml` in project directory
- ✅ **DO**: Use environment variables for secrets
- ✅ **DO**: Provide instructions for user to copy to `~/.mxcp/` if they want
- ❌ **DON'T**: Edit or modify `~/.mxcp/config.yml`
- ❌ **DON'T**: Assume location of user's global config

**Reasoning**:
- User maintains control over their global configuration
- Project remains self-contained and portable
- Safer for automated agents
- User can review before integrating into global config

See **references/project-selection-guide.md** (Configuration Management section) for complete details.

## Database Configuration

**CRITICAL: ALWAYS use the default database path `data/db-default.duckdb`**

- ✅ **DO**: Use `data/db-default.duckdb` as the database path (MXCP default)
- ✅ **DO**: Create the `data/` directory if it doesn't exist
- ❌ **DON'T**: Create random or numbered database names (e.g., `db1.duckdb`, `mydb.duckdb`)
- ❌ **DON'T**: Use different database paths unless the user explicitly requests it

**How MXCP configures the database:**

MXCP auto-generates `profiles.yml` with this default:
```yaml
# profiles.yml (auto-generated by mxcp dbt-config)
my_project:
  outputs:
    dev:
      type: duckdb
      path: "{{ env_var('MXCP_DUCKDB_PATH', 'data/db-default.duckdb') }}"
  target: dev
```

**To override the database path**, set the environment variable:
```bash
export MXCP_DUCKDB_PATH=data/db-default.duckdb
```

**When using dbt**, run `mxcp dbt-config` to generate the correct profiles.yml automatically.

## Core Concepts

### What is MXCP?

Use MXCP's **structured methodology** for building production MCP servers:

1. **Data Quality First**: Start with dbt models and data contracts
2. **Service Design**: Define types, security policies, and API contracts
3. **Smart Implementation**: Choose SQL for data, Python for logic
4. **Quality Assurance**: Validate, test, lint, and evaluate
5. **Production Operations**: Monitor drift, track audits, ensure performance

### Implementation Languages

Choose the appropriate language for each task:

- **SQL**: Use for data queries, aggregations, joins, filtering
- **Python**: Use for complex logic, ML models, API calls, async operations
- **Both**: Combine in the same project as needed

### Project Structure

**CRITICAL: MXCP enforces this directory structure. Files in wrong directories are ignored.**

```
mxcp-project/
├── mxcp-site.yml       # Project configuration (required)
├── tools/              # MCP tool definitions (.yml) - MUST be here
├── resources/          # MCP resource definitions (.yml) - MUST be here
├── prompts/            # MCP prompt definitions (.yml) - MUST be here
├── evals/              # LLM evaluation tests (.yml)
├── python/             # Python endpoints and shared code
├── plugins/            # MXCP plugins for DuckDB
├── sql/                # SQL implementation files
├── drift/              # Drift detection snapshots
├── audit/              # Audit logs (when enabled)
├── models/             # dbt models (optional)
└── target/             # dbt target directory (optional)
```

**Directory Rules**:
- Tools MUST be in `tools/*.yml` (not in root or other directories)
- Resources MUST be in `resources/*.yml`
- Prompts MUST be in `prompts/*.yml`
- SQL implementations should be in `sql/*.sql` and referenced via relative paths
- Use `mxcp init --bootstrap` to create proper structure

## Decision Framework

**When building MXCP servers, follow this decision tree:**

### Step 1: Understand the Technical Requirements

**If technical details are unclear**, ask clarifying questions about implementation:
- What type of data source? (CSV, API, database, etc.)
- Authentication mechanism? (OAuth, token, none)
- Access control needs? (public, role-based, user-specific)
- Data sensitivity? (PII, credentials, financial)

**Important**: These questions clarify the **technical implementation approach**, not the business requirements. If the user's functional requirements are unclear (e.g., "what should this tool do?"), ask them to clarify their business needs first.

**If no interaction available**, use technical heuristics from **references/project-selection-guide.md**

### Step 2: Select Approach

Consult **references/project-selection-guide.md** for:
- Decision tree based on data source type
- Template selection (if applicable)
- Implementation patterns
- Security requirements

### Step 3: Common Patterns & Templates

**CSV File → MCP Server**:
- **Template**: `assets/project-templates/covid_owid/` (complete CSV + dbt example)
- **Steps**:
  1. Place CSV in `seeds/` directory
  2. Create `seeds/schema.yml` with column definitions and tests
  3. Run `dbt seed` to load into DuckDB
  4. Create SQL tool with `SELECT * FROM <table>`
  5. Add parameters for filtering/pagination
  6. Test with `dbt test` and `mxcp test`

**API Integration → MCP Server**:
- **Templates**:
  - OAuth: `google-calendar/`, `jira-oauth/`, `salesforce-oauth/`
  - Token: `jira/`, `salesforce/`, `confluence/`
  - SSO: `keycloak/`
- **Steps**:
  1. Check `assets/project-templates/` for matching template
  2. If found: copy template, adapt configuration
  3. If not found: use `python-demo/` template as base
  4. Implement authentication (OAuth/token)
  5. Create Python tools for API operations
  6. Add error handling and retries

**Python Tools → MCP Server**:
- **Template**: `assets/project-templates/python-demo/` (START HERE)
- **Steps**:
  1. Copy python-demo template
  2. Review example tools: `analyze_numbers`, `create_sample_data`, `process_time_series`
  3. Adapt Python functions in `python/` directory
  4. Update tool definitions in `tools/`
  5. Follow Python development workflow (black → pyright → pytest)

**Database → MCP Server**:
- **Approach 1 - Direct Query** (real-time data):
  1. Use DuckDB `ATTACH` with PostgreSQL, MySQL, SQLite, SQL Server
  2. Create SQL tools with `ATTACH IF NOT EXISTS` in tool definition
  3. Store credentials in environment variables (config.yml)
  4. Use read-only database users for security
  5. Add parameterized queries (`$param`) to prevent SQL injection

- **Approach 2 - Cached Data** (fast queries, dbt):
  1. Define external database as dbt source
  2. Create dbt model to materialize/cache data in DuckDB
  3. Run `dbt run` to fetch and cache data
  4. Run `dbt test` for data quality validation
  5. Create MXCP tools to query cached data (very fast)
  6. Create refresh tool to update cache periodically

- **Examples**:
  - **minimal-working-examples.md** - Example 6 (PostgreSQL direct), Example 7 (dbt cache)
  - **references/database-connections.md** - Complete guide with all databases

**See**:
- [Project Templates](#working-with-project-templates) for all 14 templates
- **references/project-selection-guide.md** for complete decision tree
- **references/database-connections.md** for database connection patterns

## Getting Started

### Initialize a New Project

**CRITICAL: Always use `uv` for Python environment management.**

**IMPORTANT: Project directory location**:
- If the user specifies a project name or wants a new directory, create a new directory
- If the user is already in an empty directory or wants to initialize in the current location, use the current working directory
- When in doubt, ask the user whether to create a new directory or use the current directory

```bash
# Option A: Create new project in a new directory (if user specified a project name)
mkdir my-mxcp-project && cd my-mxcp-project

# Option B: Use current working directory (if already in desired location)
# Skip the mkdir and cd commands, proceed directly to step 2

# 2. Create virtual environment with uv
uv venv

# 3. Activate virtual environment
source .venv/bin/activate  # On Unix/macOS
# OR
.venv\Scripts\activate     # On Windows

# 4. Install MXCP and development tools
uv pip install mxcp black pyright pytest pytest-asyncio pytest-httpx pytest-cov

# 5. Initialize MXCP project
mxcp init --bootstrap

# This creates:
# - mxcp-site.yml with default config
# - Organized directory structure
# - Example hello-world endpoints (SQL + Python)
# - server_config.json for Claude Desktop

# 6. Clean up example files (recommended)
# The bootstrap creates hello-world examples for learning, but should be removed for production projects
rm tools/hello_world.yml
rm sql/hello_world.sql
```

### Python Development Workflow

**ALWAYS follow this workflow when working with Python code:**

```bash
# 1. Activate virtual environment (if not already active)
source .venv/bin/activate

# 2. After creating/editing Python files, format with black
black python/

# 3. Run type checker
pyright python/

# 4. Run unit tests
pytest tests/ -v

# 5. Only after all checks pass, proceed
```

**Mandatory tooling**:
- **uv**: Virtual environment and package management
- **black**: Code formatting (run after every edit)
- **pyright**: Type checking (run after every edit)
- **pytest**: Unit testing with coverage

### Start the Server

**ALWAYS activate virtual environment before running MXCP commands:**

```bash
# Activate environment first
source .venv/bin/activate

# Start with stdio transport (for Claude Desktop)
mxcp serve

# Start with HTTP transport
mxcp serve --transport http --port 8080

# Use specific profile
mxcp serve --profile production
```

## Working with Project Templates

MXCP provides 14 complete, runnable project templates in `assets/project-templates/` for common integration scenarios. Each template includes complete tool definitions, Python implementations, configuration examples, and comprehensive READMEs.

### Available Templates

**Start here:**
- **`python-demo`** - Python endpoint patterns (START HERE for Python tools)
- **`covid_owid`** - CSV + dbt workflow (START HERE for data projects)

**By use case:**
| Category | Templates |
|----------|-----------|
| Data | `covid_owid`, `earthquakes` |
| OAuth APIs | `google-calendar`, `jira-oauth`, `salesforce-oauth` |
| Token APIs | `jira`, `salesforce`, `confluence` |
| Enterprise Auth | `keycloak` |
| Advanced | `plugin` (DuckDB plugins) |

### Using Templates

```bash
cp -r assets/project-templates/google-calendar my-project
cd my-project
uv venv && source .venv/bin/activate
uv pip install mxcp black pyright pytest pytest-asyncio pytest-httpx pytest-cov
cat README.md  # Follow template-specific setup
mxcp validate && mxcp test && mxcp serve
```

See **references/project-selection-guide.md** for detailed template selection guidance.

## Creating Endpoints

**Two types of tools:**

1. **Custom SQL/Python Tools** - Defined in `tools/*.yml` for specific use cases
2. **Generic SQL Tools** - Built-in tools (`list_tables`, `get_table_schema`, `execute_sql_query`) that allow LLMs to explore and query databases dynamically

**Enable generic SQL tools** for natural language data exploration:
```yaml
# mxcp-site.yml
sql_tools:
  enabled: true
```

### Understanding Generic SQL Tools

**When They Are Available**:
- ✅ **Runtime only** - Available when MCP server is running (via `mxcp serve` or during `mxcp evals`)
- ✅ **Can be tested with `mxcp evals`** - Evals automatically start an internal server
- ❌ **Cannot be tested with `mxcp run tool <name>`** - They don't exist as static tool definitions in `tools/` directory
- ❌ **Cannot be tested with `mxcp test`** - These are for static tool definitions only

**How LLMs Choose Between Generic vs Custom Tools**:

LLMs often **prefer generic SQL tools** (`execute_sql_query`) over custom tools because:
- Generic tools offer more flexibility (arbitrary SQL queries)
- LLMs can construct queries tailored to the specific question
- LLMs don't need to find the "right" custom tool

**When to use generic SQL tools**:
- Exploratory data analysis scenarios
- When users ask unpredictable questions
- When building a general-purpose data assistant
- For prototyping before creating custom tools

**When to disable generic SQL tools**:
- When you want LLMs to use specific custom tools
- For production systems with strict query control
- When custom tools provide better documentation/safety
- To enforce specific data access patterns

**Testing generic SQL tools with evaluations**:
```bash
# mxcp evals automatically starts its own internal server
# Just run evals directly - no need to run mxcp serve first
mxcp evals data_exploration

# Generic SQL tools will be available if sql_tools.enabled: true in mxcp-site.yml
```

**Note**: `mxcp evals` automatically starts an internal MCP server in the background. You do NOT need to run `mxcp serve` separately.

**Evaluation strategy with generic SQL tools**:

If generic SQL tools are enabled, write eval assertions that accept both approaches:

```yaml
# Allow either custom tool OR generic SQL tool
tests:
  - name: get_customer_data
    prompt: "Show me customer CUST_12345"
    assertions:
      # Don't strictly require custom tool
      # Instead, verify answer quality
      answer_contains:
        - "CUST_12345"
        - "customer"
```

Or disable generic SQL tools to force custom tool usage:
```yaml
# mxcp-site.yml
sql_tools:
  enabled: false  # LLMs must use custom tools
```

See **assets/project-templates/covid_owid/** for complete example and **references/cli-reference.md** for security considerations.

For detailed examples and patterns, see:
- **references/endpoint-patterns.md** - Tool, resource, and prompt examples
- **references/python-api.md** - Python runtime API and patterns

## Enterprise Features

### Policy Enforcement

Control access and filter data using policies:

```yaml
policies:
  input:
    - condition: "!('hr.read' in user.permissions)"
      action: deny
      reason: "Missing HR read permission"
  output:
    - condition: "user.role != 'hr_manager'"
      action: filter_fields
      fields: ["salary", "ssn"]
```

See **references/policies.md** for comprehensive policy examples.

### Audit Logging

Enable audit trails for compliance:

```yaml
# In mxcp-site.yml
profiles:
  production:
    audit:
      enabled: true
      path: audit-logs.jsonl
```

Query logs:
```bash
mxcp log --since 1h --tool employee_data
mxcp log --export-duckdb audit.db
```

### OpenTelemetry (Distributed Tracing)

Enable production observability with OpenTelemetry:

```yaml
# In mxcp-site.yml
profiles:
  production:
    telemetry:
      enabled: true
      endpoint: "http://otel-collector:4318"
```

This provides:
- Distributed tracing across your MXCP server and dependencies
- Performance metrics and monitoring
- Integration with observability platforms (Jaeger, Grafana, etc.)

### Authentication

Configure OAuth providers in project-local `config.yml`:

```yaml
# config.yml (in project directory)
mxcp: 1

profiles:
  default:
    auth:
      provider: github
      # OAuth credentials configured here or via environment variables
    secrets:
      - name: api_token
        type: env
        parameters:
          env_var: API_TOKEN

  production:
    auth:
      provider: github
```

**Usage**:
```bash
# Option 1: Use config from project directory
mxcp serve  # Automatically finds ./config.yml

# Option 2: Specify config location
MXCP_CONFIG=./config.yml mxcp serve

# Option 3: User can manually copy to ~/.mxcp/ if preferred
cp config.yml ~/.mxcp/
```

## dbt Integration

**dbt creates the tables → MXCP queries them**

**Core workflow:**
1. Place CSV in `seeds/` → Create `seeds/schema.yml` → Run `dbt seed`
2. Create models in `models/` → Run `dbt run`
3. Validate with `dbt test`
4. Create MXCP tools that query the tables

**Key concepts:**
- **Seeds** - CSV files loaded as tables
- **Models** - SQL or Python transformations
- **Schema.yml** - ALWAYS create (defines types, tests, docs)

**Quick example (CSV → tool):**
```bash
cp data.csv seeds/               # 1. Add CSV
dbt seed && dbt test             # 2. Load and validate
# 3. Create tools/query.yml with: SELECT * FROM data WHERE id = $id
```

See **references/dbt-core-guide.md** for complete guide including Python models, Excel processing, and schema.yml patterns.

## Agent-Centric Design

**Design tools that LLMs can effectively use.** Key principles:
- Build for workflows, not just data access (consolidate related operations)
- Optimize for limited context (provide `detail_level` options, human-readable identifiers)
- Design actionable error messages (include `suggestion` field)
- Use consistent naming (`get_customer_*`, `analyze_sales_*`)

See **references/agent-centric-design.md** for complete patterns.

## Documentation Quality

**Tools must be self-documenting for LLMs with zero prior context.**

Every tool needs:
- **Description**: WHAT it does, WHAT it returns, WHEN to use it
- **Parameter descriptions**: Valid values, formats, examples
- **Return type descriptions**: Describe every field

See **references/llm-friendly-documentation.md** for examples and guidelines.

## Error Handling

**Python tools must return structured errors:**
```python
return {"success": False, "error": "User not found", "error_code": "NOT_FOUND"}
```

**SQL errors are handled automatically by MXCP.**

See **references/error-handling-guide.md** for complete patterns.

## Quality Assurance

**ALWAYS run quality checks before deployment:**

```bash
# 1. Structure validation
mxcp validate              # Check YAML structure, types, required fields

# 2. Functional testing
mxcp test                  # Run all test cases
mxcp test tool <name>      # Test specific tool

# 3. Data quality (if using dbt)
dbt test                   # Run dbt data quality tests
dbt test --select <model>  # Test specific model

# 4. Metadata quality
mxcp lint                  # Check descriptions, improve documentation

# 5. LLM behavior testing
mxcp evals                     # Test how LLMs interact with tools
mxcp evals suite_name          # Test specific eval suite
mxcp evals --model gpt-4o      # Override default model
mxcp evals --json-output       # CI/CD format
```

### YAML Schema Validation

**JSON Schema Specifications for MXCP Files**

The `assets/schemas/` directory contains JSON Schema files that define the exact structure and validation rules for all MXCP YAML files:

- **mxcp-site-schema-1.json** - Validates `mxcp-site.yml` project configuration
- **mxcp-config-schema-1.json** - Validates `config.yml` authentication and secrets
- **tool-schema-1.json** - Validates tool definitions in `tools/*.yml`
- **resource-schema-1.json** - Validates resource definitions in `resources/*.yml`
- **prompt-schema-1.json** - Validates prompt definitions in `prompts/*.yml`
- **eval-schema-1.json** - Validates evaluation suites in `evals/*.yml`
- **common-types-schema-1.json** - Common type definitions used by other schemas

**When to use schema validation:**

1. **During development** - Validate YAML files as you create them to catch structure errors early
2. **Before committing** - Ensure all configuration files are valid before version control
3. **In CI/CD pipelines** - Automate validation as part of your build process
4. **When debugging** - Get detailed error messages about invalid YAML structure

**Using the validation script:**

```bash
# Validate a single YAML file
python scripts/validate_yaml.py path/to/file.yml

# Validate all MXCP YAML files in project templates
python scripts/validate_yaml.py --all

# Example output:
# ✓ assets/project-templates/jira/tools/get_issue.yml
# ✗ assets/project-templates/custom/tools/bad_tool.yml
#   Error: At tool -> parameters -> 0: 'type' is a required property
```

**How this differs from `mxcp validate`:**

- **Schema validation** (`scripts/validate_yaml.py`) - Checks YAML structure and syntax against JSON schemas (fast, no MXCP installation needed)
- **MXCP validation** (`mxcp validate`) - Full validation including SQL syntax, Python imports, parameter types, and business logic (requires MXCP)

**Best practice**: Use schema validation first for quick feedback, then run `mxcp validate` for comprehensive checks.

### Creating Effective Evaluations

**Evaluations test whether LLMs can accomplish real tasks using your tools.**

```bash
# Run evaluations (automatically starts internal MCP server)
mxcp evals                    # Run all evals
mxcp evals suite_name         # Run specific suite
mxcp evals --model gpt-4o     # Override model
```

**Quick eval file format** (`evals/my-evals.yml`):
```yaml
mxcp: 1
suite: my_tests
tests:
  - name: basic_test
    prompt: "What customers are at risk?"
    assertions:
      must_call:
        - tool: analyze_churn
      answer_contains: ["risk"]
```

**Key considerations**:
- Evals are non-deterministic - LLMs may behave differently each run
- LLMs may prefer generic SQL tools over custom tools if `sql_tools.enabled: true`
- Use relaxed assertions (`args: {}`) over strict ones for reliability

See **references/mxcp-evaluation-guide.md** for complete guide including model configuration, assertion types, and troubleshooting.

**Security validation checklist:**
- [ ] All SQL queries use parameterized variables (`$param`)
- [ ] Authentication configured for all endpoints requiring it
- [ ] Policies defined for sensitive data access
- [ ] Secrets stored in Vault/1Password (never in code)
- [ ] Input validation on all parameters
- [ ] Audit logging enabled for production

**Robustness validation checklist:**
- [ ] Error handling in Python endpoints (try/except)
- [ ] NULL handling in SQL queries
- [ ] Type validation in all tool definitions
- [ ] Return type specifications complete
- [ ] Test cases cover edge cases (empty, null, invalid)

**Before deployment workflow:**
```bash
# Run full validation suite
mxcp validate && mxcp test && mxcp lint

# For dbt projects, also run:
dbt test

# Create drift baseline before first deployment
mxcp drift-snapshot

# Enable audit logging for production
# In mxcp-site.yml profiles.production:
#   audit:
#     enabled: true
```

For comprehensive testing guidance, see **references/testing-guide.md**.

## CLI Commands Reference

### Core Commands
- `mxcp init [--bootstrap]` - Initialize new project
- `mxcp serve` - Start MCP server
- `mxcp list` - List all endpoints
- `mxcp run tool NAME --param key=value` - Execute endpoint

### Quality Commands
- `mxcp validate` - Check structure
- `mxcp test` - Run tests
- `mxcp lint` - Check metadata
- `mxcp evals` - Test LLM behavior

### Data Commands
- `mxcp query "SQL"` - Execute SQL
- `mxcp dbt run` - Run dbt
- `mxcp drift-snapshot` - Create baseline
- `mxcp drift-check` - Detect changes

### Monitoring Commands
- `mxcp log [--since 1h]` - Query audit logs
- `mxcp log-cleanup` - Apply retention

For complete CLI documentation, see **references/cli-reference.md**.

## Troubleshooting

For comprehensive debugging guidance, see **references/debugging-guide.md**.

**Quick debug workflow:**
```bash
mxcp validate --debug  # Check YAML structure
mxcp test --debug      # Check logic/SQL
mxcp run tool NAME --param key=value --debug  # Manual test
```

**Common quick fixes:**
- `required: true` error → Remove `required:` field, use `default: null` for optional params
- `tool:` not found → Add `tool:` wrapper after `mxcp: 1`
- `language:` vs `type:` → Use `language: python` for Python tools
- Type mismatch → Use `number` instead of `integer` for DuckDB numeric columns

## Best Practices

1. **Project Structure** - Follow organized directory layout
2. **Type Safety** - Define all parameter and return types
3. **Security** - Use Vault/1Password, never commit secrets
4. **Testing** - Write tests for all endpoints
5. **Documentation** - Add descriptions, run `mxcp lint`
6. **Performance** - Use SQL for queries, Python for logic
7. **Development Workflow**:
   ```bash
   mxcp validate && mxcp test && mxcp lint  # Development
   mxcp drift-snapshot && mxcp evals        # Before deployment
   mxcp drift-check && mxcp log --since 24h # Production
   ```

## Additional Resources

### Learn by Example (Start Here!)

**Complete Project Templates** (14 runnable examples):
- **assets/project-templates/** - Copy, customize, and run
  - `python-demo/` - Python endpoint patterns (START HERE for Python)
  - `covid_owid/` - CSV + dbt workflow (START HERE for data)
  - `google-calendar/` - OAuth integration example
  - See [Project Templates](#working-with-project-templates) for all 14 templates

**Minimal Working Examples**:
- **references/minimal-working-examples.md** - Guaranteed-to-work code snippets

### Reference Files Index

**Quick lookup by topic:**

| Topic | Reference File |
|-------|----------------|
| Validation errors | references/debugging-guide.md |
| Testing (MXCP + pytest) | references/comprehensive-testing-guide.md |
| LLM evaluations | references/mxcp-evaluation-guide.md |
| Tool/resource examples | references/endpoint-patterns.md |
| Tool templates | references/tool-templates.md |
| Python patterns | references/python-api.md |
| dbt workflows | references/dbt-core-guide.md |
| Database connections | references/database-connections.md |
| DuckDB features | references/duckdb-essentials.md |
| Error handling | references/error-handling-guide.md |
| Project selection | references/project-selection-guide.md |
| Policies | references/policies.md |
| Type system | references/type-system.md |
| CLI commands | references/cli-reference.md |

**Critical references (read first for new projects):**
- **references/build-and-validate-workflow.md** - Mandatory validation workflow
- **references/agent-centric-design.md** - Design tools LLMs can use effectively
- **references/minimal-working-examples.md** - Guaranteed working code snippets
