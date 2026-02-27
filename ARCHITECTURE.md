# Architecture

## Overview

This repository is a Claude Code plugin marketplace published by RAW Labs, providing expert guidance for building production MCP servers using the MXCP framework.

```
raw-labs-claude-marketplace/
├── .claude-plugin/
│   └── marketplace.json          # Marketplace manifest — points to plugin directories
├── plugins/
│   └── mxcp-plugin/              # MXCP server development
│       ├── .claude-plugin/plugin.json
│       └── skills/mxcp-expert/
├── CLAUDE.md                     # Project-level instructions for Claude
├── README.md                     # User-facing documentation
├── CHANGELOG.md                  # Version history
├── TODO.md                       # Tracked work items
├── AGENTS.md                     # Agent documentation and maintenance guide
└── ARCHITECTURE.md               # This file
```

## Plugins

### mxcp-plugin (v1.0.0)

Expert guidance for building MXCP servers. Single skill, large reference library.

```
plugins/mxcp-plugin/skills/mxcp-expert/
├── SKILL.md                      # Skill definition + navigation table
├── references/                   # 50 docs organized by topic
│   ├── concepts/                 # Endpoints, project structure, type system
│   ├── getting-started/          # Quickstart, introduction, glossary
│   ├── tutorials/                # Hello world, SQL/Python endpoints
│   ├── schemas/                  # Tool, resource, prompt, site-config YAML schemas
│   ├── reference/                # CLI, common tasks, plugins, SQL/Python reference
│   ├── integrations/             # Claude Desktop, dbt, DuckDB, Excel
│   ├── operations/               # Deployment, monitoring, drift detection, config
│   ├── security/                 # Authentication, policies, auditing
│   ├── quality/                  # Testing, linting, evals, validation
│   └── examples/                 # Analytics, customer service, data management
├── assets/project-templates/     # 11 starter templates
│   ├── confluence, covid_owid, earthquakes, google-calendar
│   ├── jira, jira-oauth, keycloak, plugin
│   ├── python-demo, salesforce, salesforce-oauth
└── scripts/
    └── validate_yaml.py          # YAML validation utility
```

## Key Design Decisions

**Progressive Disclosure in mxcp-expert:** The 50 reference files are organized by topic and loaded on-demand. SKILL.md has a navigation table pointing to the right reference for each task. This keeps the context window lean — Claude only loads the references it needs.
