---
approved: true
backlog: backlog/agent-mode-compat.md
approved_at: 2026-04-14

---

# agent-mode-compat — Non-Claude Model Compatibility

## Problem

The `model: sonnet/haiku` frontmatter in agent files and skills is Claude-specific. When running under `glm-5.1:cloud` or other non-Claude models, the model tier is silently ignored. The `--agent` flag and `make zie-implement` invoke `claude --agent zie-framework:zie-implement-mode`, which is a Claude Code CLI feature that may fail on non-Claude providers.

Users on non-Claude models cannot use `/implement` via `make zie-implement` and the `model:` frontmatter gives false expectations about model routing.

## Approach

Add documentation about non-Claude model limitations. Add a fallback Makefile target that works without the `--agent` flag. Add a detection mechanism in `/implement` that falls back gracefully when `--agent` mode is unavailable.

## Components

### 1. Document non-Claude model limitations

**File**: `CLAUDE.md` — Add a new section after "Tech Stack":

```markdown
## Non-Claude Model Compatibility

- `model:` frontmatter in agent/skill files is a Claude Code hint — non-Claude providers ignore it
- `--agent` flag requires Claude Code CLI — use `make implement-local` on non-Claude providers
- `effort:` frontmatter has no effect on non-Claude models
- Safety hooks (safety_check_agent.py) fall back to regex when Claude models are unavailable (ADR-066)
```

**File**: `zie-framework/project/context.md` — Add a compatibility note.

### 2. Add fallback invocation in /implement

**File**: `commands/implement.md`

Change the pre-flight agent mode advisory (Step 0) from:

```markdown
0. **Pre-flight: Agent mode advisory** — if not running with `--agent zie-framework:zie-implement-mode`:
   print `ℹ️ Tip: run inside \`claude --agent zie-framework:zie-implement-mode\` for best results.`
   (advisory only — do not block, continue immediately)
```

To:

```markdown
0. **Pre-flight: Agent mode advisory** — if not running with `--agent zie-framework:zie-implement-mode`:
   print `ℹ️ Tip: run inside \`claude --agent zie-framework:zie-implement-mode\` for best results.
   On non-Claude models, use \`make implement-local\` instead.`
   (advisory only — do not block, continue immediately)
```

### 3. Make model: frontmatter optional (documentation only)

**File**: `agents/zie-implement-mode.md` — Add a comment:
```markdown
<!-- model: sonnet — hint for Claude Code; ignored by non-Claude providers -->
```

**File**: `agents/zie-audit-mode.md` — Same comment.
**File**: `agents/zie-release-mode.md` — Same comment.

### 4. Add make implement-local target

**File**: `Makefile`

Add after the `zie-implement` target:

```makefile
implement-local: ## Run /implement in current session (no --agent flag, works on non-Claude providers)
	@echo "[zie-framework] Running /implement in current session (no agent mode)"
	@echo "[zie-framework] On Claude Code, prefer: make zie-implement"
```

This is a documentation-only target — the actual implementation runs in the current Claude session via `/implement` command, not via a subshell.

### 5. Update ADR-066

**File**: `zie-framework/decisions/ADR-066-non-claude-model-compatibility.md`

Add a section documenting the agent mode limitation and the `implement-local` fallback.

## Data Flow

No data flow changes — this is a documentation and UX improvement.

## Edge Cases

- **Claude Code with --agent**: Works as before (no change)
- **Non-Claude provider without --agent**: `/implement` command works in current session; advisory message points to `make implement-local`
- **Non-Claude provider with --agent attempted**: Claude Code CLI may not exist; the Makefile target is a no-op documentation target that prints guidance

## Out of Scope

- Changing agent file frontmatter format
- Adding runtime model detection
- Modifying the safety hook behavior (already handled by ADR-066)

## Testing

- Verify `CLAUDE.md` includes non-Claude compatibility section
- Verify `commands/implement.md` includes `make implement-local` tip
- Verify `Makefile` includes `implement-local` target
- Verify agent files include the optional model hint comment