---
approved: true
approved_at: 2026-03-24
backlog: backlog/plugin-mcp-bundle.md
---

# Plugin .mcp.json Bundle zie-memory Server — Design Spec

**Problem:** Users must manually configure the zie-memory MCP server in every project, creating friction that prevents zero-setup brain integration when zie-framework is installed as a plugin.

**Approach:** Add a `.mcp.json` file at the plugin root (`.claude-plugin/`) declaring the zie-memory MCP server. Claude Code loads this file automatically when the plugin is enabled, making zie-memory available without any per-project manual configuration. The server entry is gated on `ZIE_MEMORY_API_URL` being set in the environment — if absent, the server declaration is present but the server fails to start gracefully, which is the same behavior users already have with the existing HTTP-based fallback. Skills that call `mcp__zie-memory__*` tools are updated to use the MCP tool names directly when `zie_memory_enabled=true`, consolidating the two existing integration paths (HTTP API via hooks, MCP tools via commands) into a single MCP-first path.

**Components:**
- `.claude-plugin/.mcp.json` — new file; declares `zie-memory` MCP server using `npx zie-memory` (stdio transport) with `ZIE_MEMORY_API_URL` and `ZIE_MEMORY_API_KEY` passed as env vars
- `.claude-plugin/plugin.json` — no changes required; `.mcp.json` is auto-discovered at plugin root by Claude Code
- `skills/spec-design/SKILL.md` — update `recall`/`remember` pseudo-calls to reference canonical `mcp__plugin_zie-memory_zie-memory__recall` and `mcp__plugin_zie-memory_zie-memory__remember` tool names in the `zie_memory_enabled=true` branches
- `skills/write-plan/SKILL.md` — same MCP tool name update
- `skills/debug/SKILL.md` — same MCP tool name update
- `skills/verify/SKILL.md` — same MCP tool name update
- `commands/zie-backlog.md` — same MCP tool name update for recall + remember steps
- `commands/zie-spec.md` — same MCP tool name update
- `commands/zie-plan.md` — same MCP tool name update
- `commands/zie-implement.md` — same MCP tool name update
- `commands/zie-fix.md` — same MCP tool name update
- `commands/zie-release.md` — same MCP tool name update
- `commands/zie-retro.md` — same MCP tool name update
- `commands/zie-init.md` — update step 12 memory bootstrap call; also set `zie_memory_enabled=true` in `.config` if `ZIE_MEMORY_API_URL` is set (already done) — no logic change needed, just MCP tool name
- `templates/.config.template` — no change; `zie_memory_enabled` field remains; detection logic in `zie-init` stays env-based
- `hooks/session-resume.py` — no change; `zie_memory_enabled` flag in `.config` still controls the "Brain: enabled/disabled" status line; hooks use HTTP API path independently of the MCP bundle
- `hooks/utils.py` — no change; `call_zie_memory_api()` remains for hook HTTP path (hooks cannot invoke MCP tools)
- `README.md` — add section: "Brain Integration — zero-setup via plugin .mcp.json"
- `tests/test_mcp_bundle.py` — new test file; see Tests section below

**Data Flow:**

1. User installs zie-framework plugin (`claude plugin add zie-framework`).
2. Claude Code discovers `.claude-plugin/.mcp.json` at plugin root and registers the `zie-memory` MCP server entry.
3. On session start, Claude Code attempts to launch `zie-memory` via stdio. If `ZIE_MEMORY_API_URL` is not set, the server process exits immediately (existing zie-memory behavior) — Claude Code logs a warning but the session continues unblocked.
4. If `ZIE_MEMORY_API_URL` is set, zie-memory server starts successfully. The MCP tools `mcp__plugin_zie-memory_zie-memory__recall`, `mcp__plugin_zie-memory_zie-memory__remember`, `mcp__plugin_zie-memory_zie-memory__briefing`, etc. become available to Claude.
5. `zie-init` runs on the project. It checks `ZIE_MEMORY_API_KEY` env var → sets `zie_memory_enabled=true` in `.config`. No additional MCP configuration step needed.
6. When a command (e.g., `/zie-spec`) reads `.config` and finds `zie_memory_enabled=true`, it calls `mcp__plugin_zie-memory_zie-memory__recall` directly as a tool call — no intermediary HTTP request or pseudo-API syntax.
7. Skills that declare `zie_memory_enabled: true` in frontmatter receive the flag from the invoking command and apply the same MCP tool calls in their `zie_memory_enabled=true` branches.
8. Hook path is unchanged: `wip-checkpoint.py` and `session-learn.py` continue to call `call_zie_memory_api()` over HTTPS — hooks cannot invoke MCP tools, so the HTTP path is the correct path for hook-originated writes.
9. On session stop, `session-learn.py` fires the HTTP `/api/hooks/session-stop` endpoint as before — this is independent of the MCP bundle.

**Edge Cases:**
- `ZIE_MEMORY_API_URL` not set: zie-memory MCP server fails to start; Claude Code session continues normally; all `zie_memory_enabled=true` branches are skipped because `zie-init` wrote `zie_memory_enabled=false`; no user-visible error beyond Claude Code's own server-launch warning.
- `ZIE_MEMORY_API_URL` set but server unreachable at runtime: MCP tool call returns an error; commands and skills must treat a tool error as equivalent to `zie_memory_enabled=false` for that call — log a stderr warning and continue.
- Plugin not installed (user runs zie-framework commands from a local `.claude/` copy without plugin install): `.mcp.json` not loaded; MCP tools unavailable; graceful degradation applies — same as no-URL case.
- `ZIE_MEMORY_API_KEY` set without `ZIE_MEMORY_API_URL`: `call_zie_memory_api()` guards already check `api_url.startswith("https://")` before calling — no regression. `.mcp.json` server entry still needs both vars to function; server may start but auth will fail on first tool call.
- Duplicate MCP server registration: if user has manually added `zie-memory` to their project `.mcp.json`, both entries coexist. Claude Code deduplicates by server name — the project-level entry takes precedence (standard Claude Code plugin/project MCP merge behavior).
- Agent scoping: reviewer skills (`spec-reviewer`, `plan-reviewer`, `impl-reviewer`) run as subagents. They inherit the parent session's MCP servers, including zie-memory — no per-agent `mcpServers:` frontmatter needed at this time. Deferring agent-scoped MCP to a future backlog item.
- `.mcp.json` syntax error at plugin root: Claude Code logs a parse error and skips the file; plugin continues to load (hooks and commands are unaffected); zie-memory MCP is simply unavailable.

**Out of Scope:**
- Scoping zie-memory MCP to specific reviewer agents via `mcpServers:` in agent frontmatter — deferred; current inheritance model is sufficient.
- Changing the hook HTTP path (`call_zie_memory_api`) to use MCP tools — hooks execute outside the Claude tool-call context and cannot invoke MCP tools.
- Bundling any MCP servers other than zie-memory in this `.mcp.json`.
- Changing how `ZIE_MEMORY_API_URL` / `ZIE_MEMORY_API_KEY` are sourced (env var approach is correct; no `.env` file loading added).
- Auto-installing the zie-memory npm package if missing — that is a user responsibility documented in README.
- Migrating existing `.config` files in deployed projects — `zie_memory_enabled` is already set by `zie-init` using env detection; no migration needed.

## Tests

`tests/test_mcp_bundle.py` must cover:

1. **Schema validity** — `.claude-plugin/.mcp.json` parses as valid JSON; top-level key is `mcpServers`; `zie-memory` entry has `type`, `command`, and `env` keys.
2. **Required env vars declared** — `zie-memory` server entry declares `ZIE_MEMORY_API_URL` and `ZIE_MEMORY_API_KEY` in its `env` map.
3. **Graceful missing server** — a subprocess call to the server command with no env vars set exits without hanging (timeout 3s); confirms zie-memory exits cleanly when unconfigured.
4. **Plugin.json unaffected** — `.claude-plugin/plugin.json` still parses correctly after adding `.mcp.json`; no required fields removed.
