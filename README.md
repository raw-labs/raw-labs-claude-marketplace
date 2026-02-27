# RAW Labs Marketplace for Claude

RAW Labs Marketplace for Claude plugins.

Community-driven marketplace, so feel free to use and contribute!

## Getting Started

### Install Claude Code

**macOS/Linux:**
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows:**
```powershell
irm https://claude.ai/install.ps1 | iex
```

### Add This Marketplace

```bash
/plugin marketplace add raw-labs/raw-labs-claude-marketplace
```

## Plugins

### mxcp-plugin

Expert guidance for building production MCP servers using the MXCP framework.

| Skill | Description |
|-------|-------------|
| **mxcp-expert** | SQL/Python endpoint development, authentication, deployment, with 50 reference docs and 11 project templates |

```bash
/plugin install mxcp-plugin@raw-labs-claude-marketplace
```

**Example prompt:**
```
Create an MXCP server that connects to my PostgreSQL database and
provides tools for querying customer orders.
```

The skill covers SQL and Python endpoints, OAuth authentication, testing and validation, deployment, and monitoring.

Or use interactive mode:
```bash
/plugin
```

**Tip:** In interactive mode, press `SPACE` to select the plugin before confirming.

**Important:** Restart Claude Code after installing for changes to take effect.

## Best Practices

### Be Specific
- Point to files: "Use sales.xlsx in ./data/" not "use the Excel file"
- Explain the goal: "I need to query total sales by region"
- Provide context: Share schema, examples, or existing patterns

### Stay Engaged
- Interrupt if off-track: "Stop. That's not what I need."
- Review changes before accepting
- Iterate: "Good, now add error handling"

### Provide Examples
- Show desired output format
- Share similar code you like
- Reference documentation to follow

## Update

Update marketplace:
```bash
/plugin marketplace update raw-labs-claude-marketplace
```

Update a plugin:
```bash
/plugin update mxcp-plugin@raw-labs-claude-marketplace
```

## Resources

- [RAW Labs](https://www.raw-labs.com/)
- [MXCP Quickstart](https://mxcp.dev/getting-started/quickstart/)
- [MXCP Documentation](https://mxcp.dev)
- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [Plugin Marketplace Docs](https://docs.anthropic.com/en/docs/claude-code/plugins)
