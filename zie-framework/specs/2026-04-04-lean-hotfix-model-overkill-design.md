# Lean Hotfix Model Overkill — Design Spec

**Problem:** `commands/hotfix.md` declares `model: claude-opus-4-6` and `effort: high` for a 5-step mechanical emergency fix track, while the fuller `/fix` command (regression test + verify skill + ROADMAP write) uses `model: sonnet` and `effort: medium` — the cost/complexity assignment is inverted.

**Approach:** Swap the frontmatter values in `commands/hotfix.md` to `model: claude-sonnet-4-6` and `effort: low`. No logic changes — the fix is purely in the YAML frontmatter. Sonnet is sufficient for the mechanical steps (open drift log, describe problem, fix, close log, ship); none of those steps require extended thinking or Opus-level reasoning.

**Components:**
- `commands/hotfix.md` — only file changed (two frontmatter keys)

**Data Flow:**
1. Claude Code reads `commands/hotfix.md` frontmatter when `/hotfix` is invoked.
2. `model: claude-sonnet-4-6` is selected instead of Opus.
3. `effort: low` suppresses extended thinking budget.
4. The 5 hotfix steps execute identically — only the model and effort tier change.

**Edge Cases:**
- No runtime logic depends on the model or effort values — change is safe.
- Tests that assert frontmatter fields (lint checks) must accept `claude-sonnet-4-6` and `low` as valid values.

**Out of Scope:**
- Changing the `/hotfix` step logic or narrative content.
- Updating `/fix`, `/implement`, or any other command.
- Introducing a configuration override for model selection in `.config`.
