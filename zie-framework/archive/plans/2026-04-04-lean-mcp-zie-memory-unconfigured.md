---
slug: lean-mcp-zie-memory-unconfigured
date: 2026-04-04
approved: true
approved_at: 2026-04-04
model: sonnet
effort: low
---

# Plan: lean-mcp-zie-memory-unconfigured

## Goal

Audit all commands and skills that call `mcp__plugin_zie-memory_zie-memory__*` tools. Wrap any unguarded call in `If zie_memory_enabled=true:` conditional. Verify already-guarded calls remain correct.

## Tasks

### Task 1 — Audit files for unguarded MCP calls

**Files to audit:**

- `commands/backlog.md` — verify recall (Step 3) and remember (Step 7) are guarded
- `commands/fix.md` — verify recall (Step 4) and remember are guarded
- `commands/implement.md` — verify recall and brain write are guarded
- `commands/plan.md` — verify Phase B recall and remember are guarded
- `commands/release.md` — verify recall + remember at Step 9 are guarded
- `commands/retro.md` — verify recall (Phase 1), remember (Phase 4), self-tuning section are guarded
- `commands/init.md` — verify remember at Step 13 is guarded
- `commands/spec.md` — delegates to skill; verify delegation note is accurate
- `skills/spec-design/SKILL.md` — verify recall in "เตรียม context" and remember at Step 7 are guarded

Search command:
```bash
grep -rn "mcp__plugin_zie-memory" commands/ skills/ --include="*.md"
```

### Task 2 — Wrap unguarded calls

**Pattern to apply** for any unguarded call found:

Before:
```markdown
Call `mcp__plugin_zie-memory_zie-memory__remember` with ...
```

After:
```markdown
If `zie_memory_enabled=true` (from `zie-framework/.config`):
  Call `mcp__plugin_zie-memory_zie-memory__remember` with ...
```

Apply to every unguarded instance found in Task 1.

### Task 3 — Verify `.config` read in each command

For each command that has MCP calls, confirm it reads `zie-framework/.config` near the top and extracts `zie_memory_enabled` (default `false`). If not present, add:

```markdown
Read `zie-framework/.config` → `zie_memory_enabled` (default: `false`).
```

### Task 4 — Run tests

```bash
make test-unit
```

Existing tests must pass. No new tests required (spec says "No tests beyond existing command-flow unit tests").

## Acceptance Criteria

- `grep -rn "mcp__plugin_zie-memory" commands/ skills/` shows no unguarded calls
- Every MCP call is wrapped in `If zie_memory_enabled=true:` guard
- When `zie_memory_enabled=false` (default), all MCP steps are silently skipped
- `make test-unit` passes
