## Table of Contents

- [1. Missing `tool:` Wrapper](#1-missing-tool-wrapper)
- [2. Missing Parameter Description](#2-missing-parameter-description)
- [3. Invalid Type Names](#3-invalid-type-names)
- [4. Invalid Parameter Names](#4-invalid-parameter-names)
- [5. Invalid Format Values](#5-invalid-format-values)
- [6. Both `code` and `file` in Source](#6-both-code-and-file-in-source)
- [7. Using `required: false` for Optional Parameters](#7-using-required-false-for-optional-parameters)
- [8. Missing `language: python` for Python Tools](#8-missing-language-python-for-python-tools)
- [8a. Python Function Name Must Match Tool Name](#8a-python-function-name-must-match-tool-name)
- [9. Enum with Null Default](#9-enum-with-null-default)
- [10. Invalid Test Assertions](#10-invalid-test-assertions)
- [11. Type Mismatch with SQL Aggregates](#11-type-mismatch-with-sql-aggregates)
- [12. Custom Authentication Instead of Built-in](#12-custom-authentication-instead-of-built-in)
- [13. Database-Specific SQL Syntax](#13-database-specific-sql-syntax)
- [14. Testing Policy Denials in YAML](#14-testing-policy-denials-in-yaml)
- [15. Enum with Optional Parameter](#15-enum-with-optional-parameter)
- [16. Invalid `mxcp-site.yml` Properties](#16-invalid-mxcp-siteyml-properties)
- [17. Using `returns:` Instead of `return:`](#17-using-returns-instead-of-return)
- [18. Declaring a Parameter the Source Never Uses](#18-declaring-a-parameter-the-source-never-uses)
- [Quick Reference](#quick-reference)

# Common Mistakes to Avoid

**Read this before creating any tools.** These mistakes cause validation errors.

## 1. Missing `tool:` Wrapper

```yaml
# WRONG
mxcp: 1
name: get_calendar
description: ...

# CORRECT
mxcp: 1
tool:
  name: get_calendar
  description: ...
```

## 2. Missing Parameter Description

```yaml
# WRONG - causes validation error
parameters:
  - name: user_id
    type: string

# CORRECT
parameters:
  - name: user_id
    type: string
    description: The unique user identifier
```

## 3. Invalid Type Names

Valid types: `string`, `number`, `integer`, `boolean`, `array`, `object`

```yaml
# WRONG
type: map      # Use 'object'
type: strng    # Typo
type: int      # Use 'integer'

# CORRECT
type: object
type: string
type: integer
```

## 4. Invalid Parameter Names

Parameter names must match `^[a-zA-Z_][a-zA-Z0-9_]*$`

```yaml
# WRONG
name: user-name    # Hyphens not allowed
name: 1st_param    # Can't start with number

# CORRECT
name: user_name
name: first_param
```

## 5. Invalid Format Values

Valid formats: `email`, `uri`, `date`, `time`, `date-time`, `duration`, `timestamp`

```yaml
# WRONG
format: datetime   # Missing hyphen

# CORRECT
format: date-time
```

## 6. Both `code` and `file` in Source

Source must have exactly one of `code` or `file`:

```yaml
# WRONG
source:
  code: "SELECT 1"
  file: "query.sql"  # Can't have both

# CORRECT
source:
  code: "SELECT 1"
# OR
source:
  file: ../sql/query.sql
```

## 7. Using `required: false` for Optional Parameters

MXCP uses `default` to make parameters optional, NOT `required: false`. A
parameter is optional when it has a `default`; otherwise it is required.

```yaml
# WRONG - `required` is not a per-parameter boolean.
# Validation fails with: "required: Input should be a valid list"
parameters:
  - name: limit
    type: integer
    required: false

# CORRECT - use default to make optional
parameters:
  - name: limit
    type: integer
    description: Max results to return
    default: 10
```

(`required` *is* a valid key, but only on an `object`-typed parameter, where it
lists which nested properties are required — e.g. `required: [host]`. It is never
a boolean on a top-level parameter.)

## 8. Missing `language: python` for Python Tools

Python tools MUST specify `language: python`:

```yaml
# WRONG - treated as SQL
tool:
  name: process_data
  source:
    file: ../python/process.py

# CORRECT
tool:
  name: process_data
  language: python
  source:
    file: ../python/process.py
```

## 8a. Python Function Name Must Match Tool Name

The Python function name MUST exactly match the `tool.name`:

```python
# tools/analyze_data.yml has: name: analyze_data

# WRONG - function name doesn't match
def analyse_data(query: str) -> dict:  # British spelling
    ...

def analyzeData(query: str) -> dict:   # camelCase
    ...

# CORRECT - function name matches tool name exactly
def analyze_data(query: str) -> dict:
    ...
```

## 9. Enum with Null Default

If `default: null`, the enum MUST include `null`:

```yaml
# WRONG - null not in enum
parameters:
  - name: status
    type: string
    enum: ["active", "inactive"]
    default: null

# CORRECT - either include null in enum
parameters:
  - name: status
    type: string
    enum: ["active", "inactive", null]
    default: null

# OR - remove default if null not allowed
parameters:
  - name: status
    type: string
    enum: ["active", "inactive"]
```

## 10. Invalid Test Assertions

Only these test assertions exist:

```yaml
# VALID assertions
tests:
  - name: test_user
    arguments: [{key: id, value: 1}]
    result: {"id": 1, "name": "Alice"}        # Exact match
    result_contains: {id: 1}                   # Partial match
    result_not_contains: ["password", "ssn"]   # Fields must NOT exist
    result_contains_item: {status: "active"}   # Array contains item
    result_contains_all: [{id: 1}, {id: 2}]    # Array contains all
    result_length: 5                           # Array length
    result_contains_text: "success"            # String contains

# WRONG - these don't exist
    expect_error: true           # NOT VALID
    result_count: 5              # NOT VALID (use result_length)
    result_count_min: 1          # NOT VALID
    result_matches: "pattern"    # NOT VALID
```

## 11. Type Mismatch with SQL Aggregates

DuckDB aggregate functions return floats. Cast to integer if needed:

```sql
-- WRONG - SUM returns float but declared as integer
SELECT SUM(quantity) as total FROM orders

-- CORRECT - cast to match declared type
SELECT CAST(SUM(quantity) AS INTEGER) as total FROM orders
SELECT CAST(COALESCE(SUM(quantity), 0) AS INTEGER) as total FROM orders
```

## 12. Custom Authentication Instead of Built-in

NEVER build custom auth. MXCP has built-in OAuth:

```yaml
# WRONG - custom API key table
tool:
  name: authenticate_user
  source:
    code: SELECT * FROM api_keys WHERE key = $api_key

# CORRECT - use built-in OAuth in ~/.mxcp/config.yml
# Then use policies for authorization
policies:
  input:
    - condition: "user.role != 'admin'"
      action: deny
```

## 13. Database-Specific SQL Syntax

DuckDB has its own SQL dialect. Verify syntax in [DuckDB docs](https://duckdb.org/docs/sql/introduction). Common issues:

```sql
-- WRONG - syntax from other databases
INSERT OR REPLACE INTO users VALUES (1, 'Alice');
INSERT OR IGNORE INTO users VALUES (1, 'Alice');

-- CORRECT - DuckDB syntax
INSERT INTO users VALUES (1, 'Alice')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;

-- OR use DELETE + INSERT
DELETE FROM users WHERE id = 1;
INSERT INTO users VALUES (1, 'Alice');
```

When in doubt, check [duckdb.md](integrations/duckdb.md) or the official DuckDB documentation.

## 14. Testing Policy Denials in YAML

Policy denial tests (where access is blocked) CANNOT be tested via YAML test assertions. Use CLI testing instead:

```yaml
# WRONG - no expect_error or similar assertion exists
tests:
  - name: guest_denied
    user_context: {role: guest}
    expect_error: true  # NOT VALID
```

```bash
# CORRECT - test denials via CLI
mxcp run tool my_tool --param id=1 --user-context '{"role": "guest"}'
# Expect: "Policy enforcement failed: ..."
```

## 15. Enum with Optional Parameter

When using enum with an optional parameter, either include `null` in enum or remove enum entirely:

```yaml
# WRONG - parameter is optional but null not in enum
parameters:
  - name: category
    type: string
    enum: [Electronics, Clothing, Food]
    default: null

# CORRECT Option 1 - include null in enum
parameters:
  - name: category
    type: string
    enum: [Electronics, Clothing, Food, null]
    default: null

# CORRECT Option 2 - remove enum, document in description
parameters:
  - name: category
    type: string
    description: "Filter by category. Valid: Electronics, Clothing, Food"
    default: null
```

## 16. Invalid `mxcp-site.yml` Properties

`mxcp-site.yml` **requires** `mxcp`, `project`, `profile`. Beyond those, it accepts
a fixed set of optional top-level keys — and **rejects any key not in the schema**
(`extra_forbidden`). The allowed optional keys are: `secrets`, `sql_tools`,
`extensions`, `paths`, `plugin`, `dbt`, `profiles`.

```yaml
# WRONG - keys that are not in the schema fail validation:
#   "Site config validation error ... extra_forbidden"
mxcp: 1
name: my-project           # Wrong key! Use 'project'
description: My project    # Not a valid key
python:                    # Not a valid key (set the dir via paths.python)
  root: python

# CORRECT - minimal required config
mxcp: 1
project: my-project
profile: default

# ALSO VALID - optional keys from the schema
sql_tools:
  enabled: true
secrets:                   # secret NAMES used by this repo
  - api_key                # the VALUE is resolved from ~/.mxcp/config.yml
paths:
  python: python           # customize component directories
extensions:
  - httpfs
```

Note the split: secret *names* are declared in `mxcp-site.yml`, but their *values*
(and the database path) live in `~/.mxcp/config.yml`. See
[site-config.md](schemas/site-config.md) for every key.

## 17. Using `returns:` Instead of `return:`

The field is `return:` (singular), not `returns:`:

```yaml
# WRONG
tool:
  name: get_user
  returns:              # Wrong! No 's'
    type: object

# CORRECT
tool:
  name: get_user
  return:               # Correct - singular
    type: object
    properties:
      id: {type: integer}
      name: {type: string}
```

## 18. Declaring a Parameter the Source Never Uses

Every declared parameter must be referenced by the implementation. For SQL, that
means a `$param` reference; otherwise validation fails with
`Parameter mismatch: ... extra={'<name>'}`.

```yaml
# tool declares two parameters
parameters:
  - {name: customer_id, type: integer, description: ID}
  - {name: region, type: string, description: Region}   # declared but unused below
```

```sql
-- WRONG - 'region' is declared but never referenced -> validation fails
SELECT * FROM customers WHERE id = $customer_id

-- CORRECT - reference every declared parameter
SELECT * FROM customers WHERE id = $customer_id AND region = $region
```

If a value is genuinely optional, drop the parameter or actually use it (e.g.
`WHERE ($region IS NULL OR region = $region)`).

## Quick Reference

| Mistake | Fix |
|---------|-----|
| Missing `tool:` wrapper | Add `tool:` before name/description |
| Missing parameter description | Add `description:` to every parameter |
| `type: int` | Use `type: integer` |
| `type: map` | Use `type: object` |
| `format: datetime` | Use `format: date-time` |
| `name: user-name` | Use `name: user_name` (no hyphens) |
| Both `code:` and `file:` | Use only one |
| `required: false` | Use `default: value` for optional params |
| Missing `language: python` | Add for Python tools |
| Python func name mismatch | Function name must match `tool.name` exactly |
| `default: null` with enum | Include `null` in enum list or remove enum |
| `expect_error`, `result_count` | Use valid assertions only |
| `SUM()` returns float | Cast: `CAST(SUM(x) AS INTEGER)` |
| Custom API key auth | Use built-in OAuth + policies |
| DB-specific SQL syntax | Verify in DuckDB docs, use `ON CONFLICT` |
| Testing policy denials | Use CLI `--user-context`, not YAML tests |
| Enum + optional param | Include `null` in enum or document in description |
| `name:` in mxcp-site.yml | Use `project:` not `name:` |
| Unknown mxcp-site.yml key | Only schema keys allowed (req: `mxcp`/`project`/`profile`; opt: `secrets`/`sql_tools`/`extensions`/`paths`/`plugin`/`dbt`/`profiles`) |
| `returns:` in tool | Use `return:` (singular, no 's') |
| `result: null` for not-found on `type: object` | Object returns raise "No results returned"; use `type: array` or test via CLI |
| Declared param unused in source | Reference every param (`$name` in SQL) or remove it |
