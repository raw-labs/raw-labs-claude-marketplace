# MXCP Expert Skill Specification

## Target

Build production-ready MCP servers using MXCP framework.

## Core Behaviors

1. **Use uv for environments** - `uv venv && source .venv/bin/activate` before any mxcp command
2. **Security First** - Authentication, policies, parameterized queries
3. **Validation Always** - Run `mxcp validate` after every change
4. **Test Everything** - Endpoint tests + dbt data tests
5. **Incremental Development** - One tool at a time, validate before next

## Workflow

Create → Validate → Implement → Test → Lint → Verify