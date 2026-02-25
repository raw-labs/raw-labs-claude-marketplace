---
title: "Reference"
description: "Complete MXCP reference: CLI commands, SQL functions, Python runtime API, plugins, and common task how-tos."
---

> **Related Topics:** [Concepts](../concepts/index.md) (understand MXCP) | [Tutorials](../tutorials/index.md) (learn by doing) | [YAML Schemas](../schemas/index.md) (configuration files) | [Quality](../quality/index.md) (testing, validation)

## Table of Contents

- [Quick Start](#quick-start)
- [Reference Topics](#reference-topics)
- [Quick Reference](#quick-reference)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [Next Steps](#next-steps)

This section provides comprehensive reference documentation for all MXCP components.

## Quick Start

**Looking for how to do something?** See [Common Tasks](../reference/common-tasks.md) - quick answers to "How do I...?" questions.

## Reference Topics

### [Common Tasks](../reference/common-tasks.md)
Quick how-to reference for frequent tasks:
- Adding authentication
- Filtering sensitive data
- Writing tests
- Configuring production

### [CLI Reference](../reference/cli.md)
Complete command-line interface documentation:
- All commands and options
- Output formats
- Environment variables
- Error handling

### [SQL Reference](../reference/sql.md)
SQL capabilities in MXCP:
- DuckDB SQL syntax
- Built-in authentication functions
- Parameter binding
- Common extensions

### [Python Reference](../reference/python.md)
Python runtime API:
- Database access (`db`)
- Configuration (`config`)
- Plugin access (`plugins`)
- Lifecycle hooks

### [Plugin Reference](../reference/plugins.md)
Plugin development guide:
- Plugin structure
- UDF definition
- Type mapping
- Authentication integration

## Quick Reference

### Common Commands

```bash
# Project management
mxcp init                   # Initialize project
mxcp init --bootstrap       # With example endpoint

# Server
mxcp serve                  # Start server (default transport)
mxcp serve --transport stdio # For Claude Desktop
mxcp serve --transport streamable-http  # HTTP API

# Development
mxcp validate               # Validate endpoints
mxcp test                   # Run tests
mxcp lint                   # Check metadata quality
mxcp list                   # List endpoints

# Execution
mxcp run tool my_tool       # Run a tool
mxcp query "SELECT 1"       # Execute SQL

# Quality
mxcp evals                  # Run LLM evaluations
mxcp drift-snapshot         # Create baseline
mxcp drift-check            # Check for drift

# Audit
mxcp log                    # Query audit logs
mxcp log-cleanup            # Apply retention

# dbt
mxcp dbt-config             # Generate dbt config
mxcp dbt run                # Run dbt models
```

### Python Runtime Quick Reference

```python
from mxcp.runtime import db, config, plugins, on_init, on_shutdown

# Database
results = db.execute("SELECT * FROM users WHERE id = $id", {"id": 123})

# Configuration
secret = config.get_secret("api_key")
setting = config.get_setting("project")

# Plugins
plugin = plugins.get("my_plugin")

# Lifecycle
@on_init
def setup():
    print("Starting")

@on_shutdown
def cleanup():
    print("Stopping")
```

### SQL Functions Quick Reference

```sql
-- Authentication (when enabled)
SELECT get_username();
SELECT get_user_email();
SELECT get_user_provider();
SELECT get_user_external_token();

-- Request headers (HTTP transport)
SELECT get_request_header('Authorization');
SELECT get_request_headers_json();

-- Parameters
SELECT * FROM users WHERE id = $user_id;
```

### Type Mapping Quick Reference

| YAML Type | Python Type | DuckDB Type |
|-----------|-------------|-------------|
| `string` | `str` | `VARCHAR` |
| `integer` | `int` | `INTEGER` |
| `number` | `float` | `DOUBLE` |
| `boolean` | `bool` | `BOOLEAN` |
| `array` | `list` | Array |
| `object` | `dict` | STRUCT/JSON |

See [Type System](../concepts/type-system.md) for format annotations, constraints, and sensitive data marking.

## Environment Variables

### Core

| Variable | Description |
|----------|-------------|
| `MXCP_DEBUG` | Enable debug logging |
| `MXCP_PROFILE` | Default profile |
| `MXCP_READONLY` | Read-only mode |
| `MXCP_DUCKDB_PATH` | Override DuckDB path |
| `MXCP_CONFIG_PATH` | User config path |

### Telemetry

| Variable | Description |
|----------|-------------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint |
| `OTEL_SERVICE_NAME` | Service name |
| `MXCP_TELEMETRY_ENABLED` | Enable/disable telemetry |

### Admin

| Variable | Description |
|----------|-------------|
| `MXCP_ADMIN_ENABLED` | Enable admin socket |
| `MXCP_ADMIN_SOCKET` | Admin socket path |

## Project Structure

```
my-project/
├── mxcp-site.yml     # Project configuration (required)
├── tools/            # Tool definitions
├── resources/        # Resource definitions
├── prompts/          # Prompt definitions
├── python/           # Python code
├── plugins/          # DuckDB plugins
├── sql/              # SQL files
├── data/             # DuckDB database files
├── evals/            # Evaluation suites
├── drift/            # Drift snapshots
├── audit/            # Audit logs
├── models/           # dbt models
└── target/           # dbt output
```

## Next Steps

- [CLI Reference](../reference/cli.md) - Full command documentation
- [SQL Reference](../reference/sql.md) - SQL capabilities
- [Python Reference](../reference/python.md) - Runtime API
- [Plugin Reference](../reference/plugins.md) - Plugin development
- [YAML Schemas](../schemas/index.md) - Configuration file schemas
