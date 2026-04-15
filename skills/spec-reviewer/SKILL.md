---
name: spec-reviewer
description: Review a design spec for completeness, clarity, and YAGNI. Returns APPROVED or Issues Found with specific feedback.
user-invocable: false
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob
argument-hint: ""
model: haiku
effort: low
---

<!-- FAST PATH -->
**Purpose:** Review a design spec for completeness, YAGNI, and testability.
**When to use fast path:** Spec is short (<40 lines) and problem/approach/components/testing sections are all present.
**Quick steps:** (1) Read spec. (2) Check 9-item Phase 2 checklist. (3) Check 3-item Phase 3 context checks. (4) Output ✅ APPROVED or ❌ Issues Found.
<!-- DETAIL: load only if fast path insufficient -->

# spec-reviewer — Design Spec Review

Subagent reviewer for design specs. Called by `spec-design` after writing the spec. Returns structured verdict.

## Input Expected

| Field | Required | Description |
| --- | --- | --- |
| Spec file path | yes | `zie-framework/specs/YYYY-MM-DD-<slug>-design.md` |
| Backlog item context | yes | Problem statement + motivation |
| context_bundle | yes | ADR + project context from caller |

## Phase 1 — Validate Context Bundle (inline)

- Required: `context_bundle` from caller → `adrs_content = context_bundle.adrs` · `context_content = context_bundle.context`
- Missing → `❌ Issues Found: context_bundle required — pass from spec-design skill (do not read from disk)`

Returns: `adrs_content`, `context_content`.

## Phase 2 — Review Checklist

1. **Problem** — Clearly stated in 1-3 sentences?
2. **Approach** — One approach chosen with rationale?
3. **Components** — All affected files/modules listed?
4. **Data Flow** — Step-by-step flow described?
5. **Edge Cases** — Known edge cases listed?
6. **Out of Scope** — Scope explicitly bounded?
7. **YAGNI** — Anything not needed for the stated problem?
8. **Ambiguity** — Requirements interpretable multiple ways without more context?
9. **Testability** — Acceptance criteria derivable from this spec?

## Phase 3 — Context Checks

Cross-reference spec against loaded bundle:

1. **File existence** — named component files that don't exist and aren't marked "Create".
2. **ADR conflict** — design decision contradicting a loaded ADR. No ADRs → skip.
3. **ROADMAP conflict** — overlap with Ready/Now item (same feature/duplicate scope). ROADMAP missing → skip.

Phase 3 issues merge into the same `❌ Issues Found` block as Phase 2.

## Output Format

All pass:
```
✅ APPROVED
```

Issues found:
```
❌ Issues Found

1. [Section] <specific issue and what to fix>
2. [Section] <specific issue and what to fix>

Fix these and re-submit for review.
```

## Max Iterations Reached

2 invocations with persistent issues → output:
```
⚠️ Max review iterations reached (2). Persistent issues:
<list remaining issues>
Next steps:
- Fix issues above, then re-run: /spec <slug>
- Or simplify spec scope and re-submit
- Or ask Zie to review the spec section manually
```

## Notes

- Be specific — don't approve vague specs
- Be concise — don't invent requirements the user didn't ask for
- Return ALL issues in one response — don't stop at the first
- Max 2 iterations: initial scan (all issues) + confirm pass. 0 issues → APPROVED immediately.