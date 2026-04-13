---
status: approved
approved_by: autonomous-sprint
approved_at: 2026-04-13
clarity: 5
backlog: backlog/fix-impl-reviewer-simplify.md
---

# Fix impl-reviewer Skill Invocation and Simplify Skill Reference — Design Spec

**Problem:** Two broken components in `commands/implement.md`:

1. **Orphaned impl-reviewer skill** — Step 4 (impl-reviewer for HIGH risk) duplicates the skill's 8-point checklist inline rather than invoking `Skill(zie-framework:impl-reviewer)`. Changes to `skills/impl-reviewer/SKILL.md` do not propagate to the command. The skill accepts no `context_bundle` parameter, so it cannot use the context loaded in step 0 of the implement command.

2. **Broken simplify skill reference** — Step 2a invokes `Skill(code-simplifier:code-simplifier)` when line delta > 50. No such skill exists. The system-level `simplify` skill is the correct target, but the reference uses the wrong identifier. At runtime, this call either fails silently or produces an error, meaning code simplification after implementation is never performed.

3. **Orphaned agent file** — `agents/impl-reviewer.md` already correctly delegates to `Skill(zie-framework:impl-reviewer)`, so it is not broken, but it should be updated to reflect the new `context_bundle` parameter.

**Approach:**

- **Reconnect impl-reviewer** — Replace the inline 8-point checklist in `commands/implement.md` step 4 with `Skill(zie-framework:impl-reviewer)` invocation, passing `context_bundle` as argument. Remove the duplicated checklist lines (79-86). Update `skills/impl-reviewer/SKILL.md` frontmatter to accept `context_bundle` via `argument-hint`, and add `context_bundle` to its "Input Expected" section.

- **Fix simplify skill reference** — Change `Skill(code-simplifier:code-simplifier)` to `Skill(simplify)` on line 71 of `commands/implement.md`. Also update the related spec `2026-04-13-simplify-post-green-design.md` AC3 to reflect the correct skill name.

- **Update agent file** — Update `agents/impl-reviewer.md` to document the `context_bundle` parameter that the skill now expects.

**Non-goals:**

- Not redesigning the impl-reviewer checklist itself
- Not changing the simplify threshold (50 lines) or simplify logic
- Not changing the risk-classification logic

**Components:**

| # | File | Change |
|---|------|--------|
| 1 | `commands/implement.md` | Replace inline checklist with `Skill(zie-framework:impl-reviewer)` call; fix simplify reference |
| 2 | `skills/impl-reviewer/SKILL.md` | Add `context_bundle` to frontmatter `argument-hint` and Input section |
| 3 | `agents/impl-reviewer.md` | Document `context_bundle` parameter |
| 4 | `zie-framework/specs/2026-04-13-simplify-post-green-design.md` | Fix `Skill(code-simplifier:code-simplifier)` → `Skill(simplify)` in AC3 |

**Data Flow (impl-reviewer reconnection):**

Current (broken):
```
4. impl-reviewer → inline 8-point checklist (duplicated from SKILL.md)
```

Proposed:
```
4. impl-reviewer → Skill(zie-framework:impl-reviewer) with context_bundle argument
   - Skill reads context_bundle from argument (fast path)
   - Falls back to disk reads if not provided
```

**Data Flow (simplify fix):**

Current (broken):
```
Skill(code-simplifier:code-simplifier)  → no such skill → fails silently
```

Proposed:
```
Skill(simplify)  → invokes system-level simplify skill → works
```

**Acceptance Criteria:**

- AC1: `commands/implement.md` step 4 invokes `Skill(zie-framework:impl-reviewer)` instead of inline checklist
- AC2: The inline 8-point checklist (lines 79-86) is removed from `commands/implement.md`
- AC3: `Skill(code-simplifier:code-simplifier)` is replaced with `Skill(simplify)` in `commands/implement.md` step 2a
- AC4: `skills/impl-reviewer/SKILL.md` accepts `context_bundle` in its `argument-hint` frontmatter and documents it in Input section
- AC5: `agents/impl-reviewer.md` mentions the `context_bundle` parameter
- AC6: `zie-framework/specs/2026-04-13-simplify-post-green-design.md` AC3 references `Skill(simplify)` instead of `Skill(code-simplifier:code-simplifier)`
- AC7: No functional change to the review checklist content or simplify threshold logic