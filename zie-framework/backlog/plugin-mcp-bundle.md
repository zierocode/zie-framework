# Backlog: Bundle MCP Servers in Plugin (.mcp.json)

**Problem:**
zie-memory integration requires users to manually configure the zie-memory MCP
server in their project. If the plugin could ship the MCP server configuration,
it would be available automatically when the plugin is installed.

**Motivation:**
Plugins support `.mcp.json` at the plugin root. MCP servers defined there are
available when the plugin is enabled, without any manual user configuration.
This would make zie-memory integration zero-setup for users who have the
server installed.

**Rough scope:**
- Create `.mcp.json` at plugin root with conditional zie-memory server config
  (only active if `ZIE_MEMORY_API_URL` is set)
- Document in README: install plugin → zie-memory available automatically
- Add `mcp__zie-memory__*` tool references where appropriate in skills
- Handle gracefully when zie-memory server is not installed (current behavior:
  hooks skip if API URL not configured)
- Consider scoping zie-memory MCP to specific agents (reviewer agents) via
  `mcpServers:` in agent frontmatter rather than globally
- Tests: .mcp.json parses, missing server graceful
