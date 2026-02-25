# Architecture

## Overview

This repository is a Claude Code plugin marketplace containing two plugins published by RAW Labs. Both plugins help users build production MCP servers using the MXCP framework.

```
raw-labs-claude-marketplace/
├── .claude-plugin/
│   └── marketplace.json          # Marketplace manifest — points to plugin directories
├── plugins/
│   ├── mxcp-plugin/              # Plugin 1: MXCP server development
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/mxcp-expert/
│   └── mxcp-data-pipeline/       # Plugin 2: Excel-to-MXCP data pipeline
│       ├── .claude-plugin/plugin.json
│       ├── agents/data-pipeline.md
│       └── skills/
│           ├── data-investigation/
│           ├── mxcp-dbt-ingest/
│           └── data-pipeline/
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

### mxcp-data-pipeline (v1.0.0)

Automated Excel-to-MXCP pipeline with self-validating investigation, dbt ingestion, and 6-layer verification. Three skills + one agent.

```
plugins/mxcp-data-pipeline/skills/data-investigation/  # Phase 1: Profile and investigate Excel
├── SKILL.md
├── assets/scripts/
│   ├── profile_excel.py          # ~800-line profiler (header detection, FK candidates, etc.)
│   └── canonical.py              # Shared utilities
└── references/
    ├── data-model-spec-format.md # Output format specification
    └── domains/                  # Domain pattern accelerators
        ├── finance.md, sales.md, hr.md, inventory.md, marketing.md

plugins/mxcp-data-pipeline/skills/mxcp-dbt-ingest/    # Phase 2: Build and verify dbt pipeline
├── SKILL.md
├── assets/project-templates/
│   └── excel-to-mxcp/           # Full project template
│       ├── scripts/             # 7 validation + generation scripts
│       ├── models/              # dbt model scaffolding (staging, intermediate, marts)
│       ├── dbt_project.yml, mxcp-site.yml, mxcp-config.yml
│       ├── Dockerfile, .github/ # Deployment artifacts
│       └── .claude/skills/      # Embedded skills for generated projects
└── references/
    ├── merged-cells.md, transposition.md
    ├── drift-detection.md, validation-patterns.md

plugins/mxcp-data-pipeline/skills/data-pipeline/      # Orchestrator skill (thin wrapper)
└── SKILL.md                      # Delegates to investigation + ingest + expert skills

plugins/mxcp-data-pipeline/agents/data-pipeline.md    # Autonomous orchestrator agent
```

## Data Flow

The mxcp-data-pipeline plugin follows a strict phased workflow:

```
Excel File
    │
    ▼
Phase 1: data-investigation
    │  Run profile_excel.py → data-profile-report.md
    │  Hypothesize PKs, FKs, calculated columns, enums
    │  Test every hypothesis against the data
    │  Output: data-model-spec.md (verified contract)
    │
    ▼  (user approval required)
Phase 2: mxcp-dbt-ingest
    │  Copy excel-to-mxcp template
    │  Generate Python models (Excel → DuckDB)
    │  Generate SQL staging/intermediate/mart models
    │  Generate dbt tests from spec
    │  Run 6-layer verification:
    │    1. Build (mxcp dbt deps + run)
    │    2. Schema tests (mxcp dbt test)
    │    3. Source-vs-target (validate_post_ingest.py)
    │    4. Schema types (validate_schema_types.py)
    │    5. Lineage (validate_lineage.py) ← requires project-manifest.md
    │    6. Drift baseline (mxcp drift-snapshot)
    │  Output: project-manifest.md
    │
    ▼  (optional)
Phase 3: mxcp-expert
    │  Design SQL/Python endpoints from mart tables
    │  Output: MXCP server ready for deployment
    │
    ▼
Production MCP Server
```

## Key Design Decisions

**Skills vs Agent:** The orchestrator exists as both a skill (`data-pipeline`) and an agent (`data-pipeline-orchestrator`). The skill is a thin wrapper with key rules. The agent has the full system prompt for autonomous operation. This avoids duplication — the agent handles end-to-end runs, while individual skills can be invoked independently for single phases.

**6-Layer Verification:** Verification is split into 6 discrete layers rather than a single "validate" step. This makes failures diagnosable — if layer 3 fails, you know source data doesn't match DuckDB, not that a type is wrong (layer 4) or lineage is broken (layer 5).

**data-model-spec.md as Contract:** The spec file is the single handoff artifact between investigation (Phase 1) and ingestion (Phase 2). Every assertion in the spec is tagged (VERIFIED, POSSIBLE, ASSUMPTION) so the ingestion phase knows what to trust.

**project-manifest.md Ordering:** The manifest must be written after layers 1-4 pass but before layer 5 (lineage validation), because `validate_lineage.py` reads the manifest to know expected row counts and documented filters.

**Progressive Disclosure in mxcp-expert:** The 50 reference files are organized by topic and loaded on-demand. SKILL.md has a navigation table pointing to the right reference for each task. This keeps the context window lean — Claude only loads the references it needs.

**Domain Patterns as Accelerators:** Domain files (finance, sales, etc.) in `data-investigation` speed up hypothesis generation but are never required. The investigation works fully without them — they just reduce the number of hypotheses to test.
