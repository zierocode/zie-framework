---
status: approved
approved_by: autonomous-sprint
approved_at: 2026-04-13
spec: zie-framework/specs/2026-04-13-fix-impl-reviewer-simplify-design.md
---

# Plan: Fix impl-reviewer Skill Invocation and Simplify Skill Reference

## Tasks

### Task 1 — Fix simplify skill reference in commands/implement.md

**File:** `commands/implement.md`
**Risk:** LOW (text-only reference change)

Change line 71 from:
```
3. If total Δ > 50 → invoke `Skill(code-simplifier:code-simplifier)` on recently modified files list
```
to:
```
3. If total Δ > 50 → invoke `Skill(simplify)` on recently modified files list
```

**AC:** AC3

### Task 2 — Replace inline checklist with Skill invocation in commands/implement.md

**File:** `commands/implement.md`
**Risk:** LOW (replaces duplicated content with delegation)

Replace the impl-reviewer step (lines 77-88). Current:

```
4. **impl-reviewer** (HIGH only): <!-- BLOCKING: do not mark task complete until all checks pass -->
   Inline review — no Skill or Agent spawn. Check changed files against:
   1. AC coverage — every acceptance criterion satisfied?
   2. Tests exist for new behavior?
   3. No over-engineering — implementation minimal for the AC?
   4. No regressions — existing contracts or interfaces broken?
   5. Code clarity — names clear, logic self-evident?
   6. Security — hardcoded secrets, command injection, SQL injection?
   7. Dead code — commented-out code or unreachable branches?
   8. ADR compliance — contradicts any `context_bundle` ADR?
   - ✅ All pass → continue
   - ❌ Issues found → auto-fix inline → `make test-unit` → if pass continue; if fail after 1 retry → surface to Zie
```

Replace with:

```
4. **impl-reviewer** (HIGH only): <!-- BLOCKING: do not mark task complete until all checks pass -->
   Invoke `Skill(zie-framework:impl-reviewer)` with `context_bundle`.
   - ✅ APPROVED → continue
   - ❌ Issues Found → auto-fix inline → `make test-unit` → if pass continue; if fail after 1 retry → surface to Zie
```

**AC:** AC1, AC2

### Task 3 — Add context_bundle parameter to skills/impl-reviewer/SKILL.md

**File:** `skills/impl-reviewer/SKILL.md`
**Risk:** LOW (additive parameter, backward-compatible)

Changes:
1. In frontmatter, change `argument-hint: ""` to `argument-hint: "context_bundle=<context_bundle>"`
2. In "Input Expected" section, add `context_bundle` as the first item:

```
- **context_bundle** (optional, preferred) — ADR + project context bundle passed from `/implement`. If provided, skip Phase 1 disk reads (fast path).
```

3. Update Phase 1 fast-path note to reference `context_bundle` parameter:
   - Current: "if context_bundle provided by caller"
   - Add clarification: "Provided via `argument-hint` when invoked from `/implement`."

**AC:** AC4

### Task 4 — Update agents/impl-reviewer.md to document context_bundle

**File:** `agents/impl-reviewer.md`
**Risk:** LOW (documentation only)

Change the invocation line from:
```
Invoke `Skill(zie-framework:impl-reviewer)` with the task description, Acceptance
Criteria, and list of files changed provided by the caller.
```
to:
```
Invoke `Skill(zie-framework:impl-reviewer)` with `context_bundle`, task
description, Acceptance Criteria, and list of files changed provided by the caller.
```

**AC:** AC5

### Task 5 — Fix simplify skill reference in simplify-post-green spec

**File:** `zie-framework/specs/2026-04-13-simplify-post-green-design.md`
**Risk:** LOW (spec documentation correction)

Change AC3 from:
```
- AC3: Step invokes `Skill(code-simplifier:code-simplifier)` when threshold exceeded
```
to:
```
- AC3: Step invokes `Skill(simplify)` when threshold exceeded
```

Also fix the data flow description on line 24 from:
```
4. If total Δ > 50 → invoke `Skill(code-simplifier:code-simplifier)` passing the list of recently modified files from step 3
```
to:
```
4. If total Δ > 50 → invoke `Skill(simplify)` passing the list of recently modified files from step 3
```

**AC:** AC6

## Verification

- `make test-unit` passes (all changes are text-only, no logic changes)
- Grep for `code-simplifier` across project — should return 0 results
- Grep for inline checklist items unique to `commands/implement.md` that duplicate `skills/impl-reviewer/SKILL.md` — should return 0 results