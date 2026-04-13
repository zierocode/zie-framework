# fix-impl-reviewer-simplify

## Problem

Two broken/semi-functional components: (a) `skills/impl-reviewer/SKILL.md` and `agents/impl-reviewer.md` are orphaned — the `/implement` command does review inline with a copy-pasted 8-point checklist instead of invoking `Skill(impl-reviewer)`. Changes to the skill file won't propagate to the command. (b) `commands/implement.md` references `Skill(code-simplifier:code-simplifier)` when line delta > 50, but no such skill exists. The `simplify` system-level skill exists but isn't referenced. At runtime, this invocation will fail silently or produce an error.

## Motivation

Orphaned skill files create maintenance debt — changes to `impl-reviewer/SKILL.md` don't affect the actual review. The broken `code-simplifier` reference means the simplify step in `/implement` never runs, so code simplification after implementation is silently skipped.

## Rough Scope

1. **Reconnect impl-reviewer** — Replace the inline 8-point checklist in `commands/implement.md` with `Skill(zie-framework:impl-reviewer)` invocation. Remove the inline checklist. Update the skill to accept `context_bundle` parameter.
2. **Fix code-simplifier reference** — Change `Skill(code-simplifier:code-simplifier)` to `Skill(simplify)` in `commands/implement.md` line 71 (or wherever the DELTA>50 check is).
3. **Clean up orphaned agent file** — Update `agents/impl-reviewer.md` to reflect that it delegates to the skill, not duplicates its logic.