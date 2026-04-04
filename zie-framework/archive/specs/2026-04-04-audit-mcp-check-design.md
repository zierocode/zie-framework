# Spec: Audit MCP Server Usage Check

**ID:** audit-mcp-check
**Date:** 2026-04-04
**Status:** Draft

## Problem

Claude Code sessions load all configured MCP servers at startup, adding context
overhead and increasing session startup latency for every server — even those
never referenced by any command or skill. There is currently no automated check
to detect MCP servers that are configured but unused.

## Motivation

Unused MCP servers silently consume context window space and slow session
initialization. A targeted check in `/zie-audit` surfaces these as actionable
findings under the Performance dimension, where context efficiency belongs.

## Design

### Where in zie-audit

Add as a sub-check inside **Agent 2 — Code Health + Performance**. Rationale:
unused MCP servers are a context efficiency / performance concern, not a
security or structural one. The check runs inline within Agent 2 — no new agent
needed.

### Detection Algorithm

1. **Locate settings files** — check both:
   - `~/.claude/settings.json` (global, expanded to absolute path)
   - `.claude/settings.json` (project-level, relative to repo root)
   Read whichever files exist. If both exist, merge their `mcpServers` keys
   (project-level takes precedence on conflicts, but union of server names is
   used for the check).

2. **Extract server names** — from the `mcpServers` object key set.
   Example: `{ "mcpServers": { "github": {...}, "postgres": {...} } }` → names
   = `["github", "postgres"]`.

3. **Grep for references** — for each server name, search for the prefix
   `mcp__<server-name>__` in:
   - `commands/*.md`
   - `skills/*/SKILL.md`
   A server is considered **used** if any match is found; **unused** otherwise.

4. **Emit findings** — for each unused server, emit a LOW severity finding:
   ```
   MCP server '<name>' configured but never referenced in commands or skills
   — consider removing to reduce context overhead
   ```
   Used servers produce no finding (clean pass).

### Graceful Skip Conditions

- Neither `~/.claude/settings.json` nor `.claude/settings.json` exists → skip
  check silently, no output.
- `mcpServers` key absent from all found settings files → skip silently.
- `mcpServers` is an empty object `{}` → skip silently.

No warning or error is emitted on skip. The check simply does not appear in
Agent 2's findings list.

### Severity

LOW — unused MCP servers do not break functionality; they reduce context
efficiency. Severity LOW keeps them out of CRITICAL/HIGH lanes but still
surfaces them as Deferred findings eligible for backlog if confirmed.

## Acceptance Criteria

| # | Criterion |
| --- | --- |
| AC1 | When a configured MCP server name has zero `mcp__<name>__` occurrences in `commands/*.md` and `skills/*/SKILL.md`, a LOW finding is emitted with the specified message. |
| AC2 | When a configured MCP server name has at least one `mcp__<name>__` occurrence in the search scope, no finding is emitted for that server. |
| AC3 | When neither `~/.claude/settings.json` nor `.claude/settings.json` exists, the check is skipped with no output. |
| AC4 | When `mcpServers` is absent or empty in all found settings files, the check is skipped with no output. |
| AC5 | The check is integrated into Agent 2 output and appears in the Phase 3 synthesis when findings exist. |
| AC6 | Multiple unused servers each produce a separate finding (one per server). |

## Out of Scope

- Checking MCP server health or connectivity.
- Detecting servers referenced in hook scripts (`hooks/*.py`).
- Distinguishing between global vs. project-level configuration for reporting
  purposes.

## Tests

Not applicable — this is a command file change (`commands/zie-audit.md`).
ACs are verified by reading the updated command and confirming the detection
logic, skip conditions, and output format match this spec.
