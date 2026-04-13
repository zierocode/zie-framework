---
status: approved
approved_by: autonomous-sprint
approved_at: 2026-04-13
---

# agent-mode-compat — Implementation Plan

## Goal

Make zie-framework usable on non-Claude model providers by documenting limitations, adding fallback invocation, and clarifying model frontmatter.

## Architecture

No architecture changes — documentation and UX improvements only.

## Tech Stack

- Markdown commands (implement.md)
- Markdown agents (zie-implement-mode.md, zie-audit-mode.md, zie-release-mode.md)
- Makefile
- CLAUDE.md
- ADR-066

### Task 1: Add non-Claude compatibility section to CLAUDE.md

**Files**: `CLAUDE.md`

**Steps**:
1. Add a "## Non-Claude Model Compatibility" section after "## Tech Stack" with:
   - `model:` frontmatter is a Claude Code hint — non-Claude providers ignore it
   - `--agent` flag requires Claude Code CLI — use `/implement` directly on non-Claude providers
   - `effort:` frontmatter has no effect on non-Claude models
   - Safety hooks fall back to regex when Claude models are unavailable (ADR-066)

**AC**:
- CLAUDE.md includes non-Claude compatibility section
- Section mentions model frontmatter, --agent flag, effort frontmatter, and ADR-066

### Task 2: Update /implement pre-flight advisory

**Files**: `commands/implement.md`

**Steps**:
1. Change Step 0 advisory from:
   ```
   print `ℹ️ Tip: run inside \`claude --agent zie-framework:zie-implement-mode\` for best results.`
   ```
   To:
   ```
   print `ℹ️ Tip: run inside \`claude --agent zie-framework:zie-implement-mode\` for best results.
   On non-Claude models, /implement works directly in the current session.`
   ```

**AC**:
- implement.md advisory mentions non-Claude models

### Task 3: Add model hint comments to agent files

**Files**: `agents/zie-implement-mode.md`, `agents/zie-audit-mode.md`, `agents/zie-release-mode.md`

**Steps**:
1. Add `<!-- model: sonnet — hint for Claude Code; ignored by non-Claude providers -->` comment after the `model:` frontmatter line in each file

**AC**:
- All three agent files have the model hint comment
- Comment explains that model frontmatter is a hint ignored by non-Claude providers

### Task 4: Add implement-local Makefile target

**Files**: `Makefile`

**Steps**:
1. Add `implement-local` target after `zie-implement`:
   ```makefile
   implement-local: ## Run /implement in current session (no --agent, works on non-Claude providers)
   	@echo "[zie-framework] Running /implement in current session (no agent mode)"
   	@echo "[zie-framework] On Claude Code, prefer: make zie-implement"
   ```

**AC**:
- Makefile has `implement-local` target
- `make implement-local` prints guidance message

### Task 5: Update ADR-066 with agent mode limitation

**Files**: `zie-framework/decisions/ADR-066-non-claude-model-compatibility.md`

**Steps**:
1. Add a section documenting that `--agent` flag is Claude Code CLI specific and the `implement-local` fallback

**AC**:
- ADR-066 documents agent mode limitation and fallback