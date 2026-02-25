# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2025-02-25

### Added
- **mxcp-data-pipeline plugin** — end-to-end Excel-to-MXCP data pipeline
  - `data-investigation` skill: self-validating Excel profiling with hypothesis testing
  - `mxcp-dbt-ingest` skill: dbt pipeline generation with 6-layer verification
  - `data-pipeline` skill: thin orchestrator coordinating the full workflow
  - `data-pipeline-orchestrator` agent: autonomous agent for pipeline execution
  - Excel profiler script (`profile_excel.py`) with header detection, FK candidates, merged cell handling, transposition detection, encoding issue flagging
  - 7 validation scripts: pre-ingest, post-ingest, schema types, lineage, dbt test generator, canonical utilities
  - `excel-to-mxcp` project template with Dockerfile, CI config, dbt scaffolding
  - Domain pattern references: finance, sales, HR, inventory, marketing
  - Reference docs: merged cells, transposition, drift detection, validation patterns

### Changed
- `mxcp-expert` skill: cleaned up all 50 reference files
  - Stripped website sidebar frontmatter from all references
  - Converted web-style links to relative markdown paths
  - Added table of contents to 28 large reference files
  - Deleted dead-weight `references/index.md`
  - Completed navigation table in SKILL.md with all doc categories
  - Expanded project templates section to list all 11 templates
- Updated `marketplace.json` with `pluginRoot`, per-plugin `version` and `keywords`

### Fixed
- Agent YAML frontmatter: use folded scalar (`description: >`) for `<example>` blocks
- 6-layer verification numbering consistency in dbt-ingest
- Table mapping derivation moved into verification flow (no more placeholders)
- Manifest ordering: write `project-manifest.md` before lineage validation

## [1.0.0] - 2024-12-22

### Added
- **mxcp-plugin** — expert guidance for building production MCP servers using MXCP
  - `mxcp-expert` skill: SQL/Python endpoint development, authentication, deployment
  - 50 reference docs covering concepts, schemas, tutorials, integrations, security, operations
  - 11 project templates: confluence, covid_owid, earthquakes, google-calendar, jira, jira-oauth, keycloak, plugin, python-demo, salesforce, salesforce-oauth
  - YAML validation script
- Initial marketplace structure and README
