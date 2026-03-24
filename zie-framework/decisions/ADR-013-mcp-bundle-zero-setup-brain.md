# ADR-013: Plugin-Bundled MCP Server for Zero-Setup Brain Integration

Date: 2026-03-24
Status: Accepted

## Context

Prior to v1.6.0, zie-memory integration required manual setup per project:
`claude mcp add zie-memory -- npx zie-memory` plus setting `zie_memory_enabled=true`
in `.config`. This was a friction point for every new project initialization. The
alternative was to require users to add the MCP server globally, but that couples
the brain integration to the user's global Claude Code config rather than the plugin.

## Decision

Ship `.claude-plugin/.mcp.json` as part of the plugin bundle. Claude Code discovers
this file at plugin load time and registers the `zie-memory` MCP server (stdio
transport, `npx zie-memory`) automatically. Environment variables
(`ZIE_MEMORY_API_URL`, `ZIE_MEMORY_API_KEY`) pass through from the shell. If the
env vars are absent, the server exits immediately — no error, no blocked session.

This makes brain integration zero-setup: install the plugin once, set the two env
vars in your shell profile, and zie-memory is available in every project session
without any per-project configuration.

## Consequences

**Positive:** Brain integration activates automatically for any project using the
plugin. No `claude mcp add` step. Graceful degradation when env vars are absent
preserves the no-brain-required contract.

**Negative:** Requires `npx zie-memory` to be resolvable at session start — the
`zie-memory` npm package must be installed globally. If absent, the server silently
fails (acceptable); if npx itself is missing, the hook log captures the error.

**Neutral:** MCP tool names in commands and skills must use the canonical
`mcp__plugin_zie-memory_zie-memory__*` format, which is verbose but unambiguous.
