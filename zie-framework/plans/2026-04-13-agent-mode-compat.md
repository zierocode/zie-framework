---
approved: true
backlog: backlog/agent-mode-compat.md
approved_at: 2026-04-14
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

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `CLAUDE.md` | Add non-Claude compatibility section with table + fallback pattern |
| Modify | `commands/implement.md` | Update pre-flight advisory for non-Claude models |
| Modify | `agents/zie-implement-mode.md` | Add model hint comment after frontmatter |
| Modify | `agents/zie-audit-mode.md` | Add model hint comment after frontmatter |
| Modify | `agents/zie-release-mode.md` | Add model hint comment after frontmatter |
| Modify | `Makefile` | Add `implement-local` target |
| Modify | `zie-framework/decisions/ADR-066-non-claude-model-compatibility.md` | Document agent mode limitation |
| Modify | `zie-framework/project/context.md` | Add non-Claude compatibility note |

## Verification Strategy (documentation-only — verify existing implementation)

All implementation was completed in v1.30.0 mega sprint. This plan documents existing implementation.

**TDD adaptation for documentation tasks:**
- **RED**: Verification step fails (grep returns non-zero)
- **GREEN**: Fix documentation or verify content exists
- **REFACTOR**: Run `make lint-md` to confirm markdown syntax

Each task uses `grep` verification + `make lint-md` instead of `make test-unit` because:
1. No unit tests exist for documentation content
2. `make lint-md` validates markdown syntax
3. `grep -q` provides binary pass/fail verification

1. Verify `CLAUDE.md` includes "## Non-Claude Model Compatibility" section
2. Verify `commands/implement.md` includes non-Claude advisory
3. Verify `Makefile` includes `implement-local` target
4. Verify agent files include model hint comment (optional)
5. Run `make lint-md` to confirm markdown syntax

---

### Task 1: Add non-Claude compatibility section to CLAUDE.md

**Files**: `CLAUDE.md`

**Steps**:
1. Add a "## Non-Claude Model Compatibility" section after "## Tech Stack" with exact content:
   ```markdown
   ## Non-Claude Model Compatibility

   Running on `glm-5.1:cloud`, Ollama, or other non-Claude providers:

   | Feature | Claude Code | Non-Claude |
   |---------|-------------|------------|
   | `model:` frontmatter | Used for model routing (ADR-012) | Ignored — runs on provider's default model |
   | `effort:` frontmatter | Routes to haiku/sonnet/opus | Ignored — no effect |
   | `--agent` flag | Available (`claude --agent`) | Unavailable — use Skill() directly |
   | Safety hooks | Claude models | Regex fallback when Claude unavailable (ADR-066) |

   **Fallback pattern:**
   ```bash
   # Claude Code: use agent mode
   claude --agent zie-framework:zie-implement-mode

   # Non-Claude: run /implement directly in current session
   /implement
   ```

   See ADR-066 for full details.
   ```

2. Verify: `grep -q "## Non-Claude Model Compatibility" CLAUDE.md`
3. Run: `make lint-md` — must PASS

**AC**:
- CLAUDE.md includes non-Claude compatibility section with table and fallback pattern
- Section mentions model frontmatter, --agent flag, effort frontmatter, and ADR-066

### Task 2: Update /implement pre-flight advisory

<!-- depends_on: Task 1 -->

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

2. Verify: `grep -q "On non-Claude models" commands/implement.md`
3. Run: `make lint-md` — must PASS

**AC**:
- implement.md advisory mentions non-Claude models

### Task 3: Verify model hint comments exist in agent files

<!-- depends_on: Task 1 -->

**Files**: `agents/zie-implement-mode.md`, `agents/zie-audit-mode.md`, `agents/zie-release-mode.md`

**Context**: Agent files already have `model:` frontmatter with `#` comment style. Verify existing format:

1. Verify all three agent files have the model hint comment:
   ```bash
   grep -l "# hint for Claude Code; ignored by non-Claude providers" agents/*.md | wc -l
   ```
   → must equal 3

2. Verify zie-release-mode.md uses `haiku` (cost optimization for release gate):
   ```bash
   grep "model: haiku" agents/zie-release-mode.md
   ```

3. Run: `make lint-md` — must PASS

**AC**:
- All three agent files have the model hint comment with `#` syntax
- Comment explains that model frontmatter is a hint ignored by non-Claude providers
- zie-release-mode.md uses `haiku` (not `sonnet`) for cost optimization

### Task 4: Add implement-local Makefile target

<!-- depends_on: Task 1 -->

**Files**: `Makefile`

**Steps**:
1. Add `implement-local` target after `zie-implement`:
   ```makefile
   implement-local: ## Run /implement in current session (no --agent, works on non-Claude providers)
   	@echo "[zie-framework] Running /implement in current session (no agent mode)"
   	@echo "[zie-framework] On Claude Code, prefer: make zie-implement"
   ```
2. Verify: `make implement-local` → must print both guidance lines
3. Run: `make lint-md` — must PASS

**AC**:
- Makefile has `implement-local` target
- `make implement-local` prints guidance message

### Task 5: Update ADR-066 with agent mode limitation

<!-- depends_on: Task 1 -->

**Files**: `zie-framework/decisions/ADR-066-non-claude-model-compatibility.md`

**Steps**:
1. Add section to ADR-066 with exact content:
   ```markdown
   ## Agent Mode Limitation

   The `--agent` flag is a Claude Code CLI-specific feature unavailable on non-Claude providers.

   **Fallback**: Use `make implement-local` or invoke `/implement` directly in the current session.

   **Detection**: Model unavailability detected via environment variable resolution; safety hooks fall back to regex when subagent model unavailable.
   ```

2. Verify: `grep -q "Agent Mode Limitation" zie-framework/decisions/ADR-066-non-claude-model-compatibility.md`
3. Run: `make lint-md` — must PASS

**AC**:
- ADR-066 documents agent mode limitation and fallback

### Task 6: Update project/context.md with non-Claude note

<!-- depends_on: Task 1 -->

**Files**: `zie-framework/project/context.md`

**Steps**:
1. Add section to `zie-framework/project/context.md` with exact content:
   ```markdown
   ## Non-Claude Model Compatibility

   When running on non-Claude providers (glm-5.1:cloud, Ollama, etc.):
   - `model:` and `effort:` frontmatter are ignored
   - `--agent` flag unavailable — use Skill() directly
   - Safety hooks use regex fallback (ADR-066)
   
   See `CLAUDE.md` for fallback patterns.
   ```

2. Verify: `grep -q "Non-Claude Model Compatibility" zie-framework/project/context.md`
3. Run: `make lint-md` — must PASS

**AC**:
- project/context.md includes non-Claude compatibility note