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

# spec-reviewer — Design Spec Review

Subagent reviewer for design specs. Called by `spec-design` after writing the
spec. Returns a structured verdict.

## Input Expected

Caller must provide:

- Path to spec file (`zie-framework/specs/YYYY-MM-DD-<slug>-design.md`)
- Backlog item context (problem statement + motivation)

## Phase 1 — Load Context Bundle

Invoke the `reviewer-context` skill to load shared context. It handles:
- **if context_bundle provided by caller** — uses `context_bundle.adrs` and
  `context_bundle.context` directly (fast path, skips disk reads)
- **If `context_bundle` absent** — read from disk: `decisions/*.md` (via
  `get_cached_adrs` cache; summary-aware: reads `ADR-000-summary.md` first,
  then calls `write_adr_cache`), `project/context.md`, `ROADMAP` lanes

Returns: `adrs_content`, `context_content`.

## Phase 2 — Review Checklist

Read the spec and check each item:

1. **Problem** — Is the problem clearly stated in 1-3 sentences?
2. **Approach** — Is one approach chosen with brief rationale?
3. **Components** — Are all affected files/modules listed?
4. **Data Flow** — Is the step-by-step flow described?
5. **Edge Cases** — Are known edge cases listed?
6. **Out of Scope** — Is scope explicitly bounded?
7. **YAGNI** — Does the spec include anything not needed for the stated problem?
8. **Ambiguity** — Are there any requirements that could be interpreted multiple
   ways without more context?
9. **Testability** — Can acceptance criteria be derived from this spec?

## Phase 3 — Context Checks

Cross-reference the spec against the loaded bundle:

1. **File existence** — list any named component files that don't exist and
   are not marked "Create" in the spec.
2. **ADR conflict** — flag any design decision in the spec that contradicts a
   loaded ADR. If no ADRs loaded → skip.
3. **ROADMAP conflict** — flag if this spec overlaps a Ready or Now item
   (same feature or duplicate scope). If ROADMAP missing → skip.

Surface Phase 3 issues in the same `❌ Issues Found` block as Phase 2 issues.

## Output Format

If all checks pass:

```text
✅ APPROVED
```

If issues found:

```text
❌ Issues Found

1. [Section] <specific issue and what to fix>
2. [Section] <specific issue and what to fix>

Fix these and re-submit for review.
```

## Max Iterations Reached

If spec-reviewer has been invoked 3 times and issues persist, output:

```text
⚠️ Max review iterations reached (3). Persistent issues:

<list remaining issues>

Next steps:
- Fix issues above, then re-run: /zie-spec <slug>
- Or simplify spec scope and re-submit
- Or ask Zie to review the spec section manually
```

## Notes

- Be specific — don't approve vague specs
- Be concise — don't invent requirements the user didn't ask for
- Return ALL issues found in this single response — do not stop at the first issue.
- Max 2 total iterations: initial scan (all issues at once) + confirm pass. If 0 issues → APPROVED immediately, no confirm pass needed.
