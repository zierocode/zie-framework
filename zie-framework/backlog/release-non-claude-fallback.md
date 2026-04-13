---
tags: [chore]
---

# Add non-Claude fallback to `/release` command

## Problem

The `/implement` command has an explicit pre-flight advisory directing non-Claude model users to invoke `/implement` directly (step 0, line 17). The `/release` command has no equivalent advisory. The `make ship` target (Makefile:75-77) tells users to "Run /zie-release for the full release gate", but `make zie-release` invokes `claude --agent zie-framework:zie-release-mode` which will silently fail on non-Claude providers.

## Motivation

Users on `minimax-m2.7:cloud` or other non-Claude models should still be able to run releases. The existing `agent-mode-compat` work (commit 77c727c) covered `/implement`, `/audit`, and the Makefile's `implement-local` target — but `/release` was missed.

## Rough Scope

1. Add non-Claude advisory to `commands/release.md` pre-flight section (mirrors what was added to `commands/implement.md`)
2. Add `make release-local` target to Makefile — equivalent to `make implement-local`, runs the release skill directly in session without `--agent`
3. Remove or generalize inline `<!-- model: sonnet reasoning -->` comments in `commands/release.md` and `skills/impl-reviewer/SKILL.md` — these imply routing that non-Claude models cannot fulfill
4. Audit `hooks/subagent-context.py` AGENT_BUDGETS for any remaining Claude-specific env var assumptions (`CLAUDE_SESSION_ID`, `CLAUDE_PLUGIN_DATA`)

## Related

- Already done: `agent-mode-compat` (commit 77c727c) — covered `/implement`, `/audit`, `make implement-local`
