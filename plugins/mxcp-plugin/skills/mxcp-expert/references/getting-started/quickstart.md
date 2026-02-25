---
title: "Quickstart"
description: "Get started with MXCP in 5 minutes. Install, create a project, and connect to Claude Desktop."
---

## Table of Contents

- [Install MXCP](#install-mxcp)
- [Create a Project](#create-a-project)
- [Run the Tool](#run-the-tool)
- [Start the Server](#start-the-server)
- [Connect to Claude Desktop](#connect-to-claude-desktop)
- [What's in the Project?](#whats-in-the-project)
- [Next Steps](#next-steps)

Get MXCP running and connected to Claude Desktop in under 5 minutes.

## Install MXCP

```bash
pip install mxcp
```

## Create a Project

Initialize a new project with a working example:

```bash
mkdir my-mxcp-project
cd my-mxcp-project
mxcp init --bootstrap
```

This creates a complete project structure with a hello world tool.

## Run the Tool

Test the example tool from the command line:

```bash
mxcp run tool hello_world --param name=World
```

Output:
```
Hello, World!
```

## Start the Server

Start the MCP server:

```bash
mxcp serve
```

The server starts in stdio mode, ready for AI client integration.

:::tip[MCP Inspector]
Use the [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) to visually test and debug your server: `npx @modelcontextprotocol/inspector`
:::

## Connect to Claude Desktop

Add MXCP to your Claude Desktop configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "my-project": {
      "command": "mxcp",
      "args": ["serve"],
      "cwd": "/absolute/path/to/my-mxcp-project"
    }
  }
}
```

Restart Claude Desktop. Ask Claude:

> "Say hello to Alice using the hello_world tool"

## What's in the Project?

The bootstrap created these files:

```
my-mxcp-project/
├── mxcp-site.yml       # Project configuration
├── tools/
│   └── hello-world.yml # Tool definition
└── sql/
    └── hello-world.sql # SQL implementation
```

**Tool definition** (`tools/hello-world.yml`):
```yaml
mxcp: 1
tool:
  name: hello_world
  description: A simple hello world tool
  parameters:
    - name: name
      type: string
      description: Name to greet
  return:
    type: string
    description: Greeting message
  source:
    file: ../sql/hello-world.sql
```

**SQL implementation** (`sql/hello-world.sql`):
```sql
SELECT 'Hello, ' || $name || '!' as greeting
```

## Next Steps

You have a working MXCP server connected to Claude Desktop. Here's where to go next:

### Build More Tools

| Tutorial | Description |
|----------|-------------|
| [SQL Endpoints](../tutorials/sql-endpoints.md) | Query databases, aggregate data |
| [Python Endpoints](../tutorials/python-endpoints.md) | Complex logic, API calls, ML models |
| [Hello World Deep Dive](../tutorials/hello-world.md) | Step-by-step first tool walkthrough |

### Add Enterprise Features

| Feature | Description |
|---------|-------------|
| [Authentication](../security/authentication.md) | OAuth with GitHub, Google, etc. |
| [Policies](../security/policies.md) | Fine-grained access control |
| [Audit Logging](../security/auditing.md) | Track all operations |

### Ensure Quality

| Tool | Description |
|------|-------------|
| [Validation](../quality/validation.md) | Verify endpoint correctness |
| [Testing](../quality/testing.md) | Unit tests for your tools |
| [Linting](../quality/linting.md) | Improve AI understanding |

### Useful Commands

```bash
mxcp validate  # Check all endpoints
mxcp test      # Run tests
mxcp lint      # Check for issues
mxcp list      # Show all endpoints
```

### Learn More

- [Introduction](../getting-started/introduction.md) - How MXCP works
- [Core Concepts](../concepts/index.md) - Endpoints, types, project structure
- [Configuration](../operations/configuration.md) - Profiles, environments
