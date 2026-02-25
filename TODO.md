# TODO

## High Priority

- [ ] Update README.md to document the mxcp-data-pipeline plugin (currently only describes mxcp-plugin)
- [ ] Add the `data-pipeline-orchestrator` agent reference to marketplace.json once agent manifest fields are supported
- [ ] Test the full Excel-to-MXCP pipeline end-to-end with a real Excel file
- [ ] Push 19 unpushed commits to origin/main

## Skills

- [ ] Add more domain patterns to `data-investigation` (e.g., healthcare, logistics, e-commerce)
- [ ] Add composite key handling to `profile_excel.py` (currently single-column PKs only)
- [ ] Add CSV/TSV support to `data-investigation` profiler (currently Excel-only)
- [ ] Add chunked reading mode for Excel files over 50MB in staging Python models
- [ ] Consider adding a `data-quality` skill for ongoing monitoring after initial pipeline build

## Agent

- [ ] Test `data-pipeline-orchestrator` agent triggering in real Claude Code sessions
- [ ] Add recovery mode integration test (existing pipeline + schema drift scenario)
- [ ] Evaluate whether `ralph-loop` integration works reliably for Phase 2 autonomous iteration

## Templates

- [ ] Update `excel-to-mxcp` template Docker image from RC tag (`0.10.0-rc12`) to stable release
- [ ] Add a multi-sheet example Excel file to the template for testing

## mxcp-expert

- [ ] Keep reference docs in sync with mxcp.dev documentation updates
- [ ] Add reference docs for new MXCP features as they ship
- [ ] Verify all 11 project templates work with latest MXCP version

## Infrastructure

- [ ] Set up CI to validate plugin structure on PR
- [ ] Add automated skill validation (frontmatter, description quality, line count)
- [ ] Consider versioning plugins independently from marketplace version
