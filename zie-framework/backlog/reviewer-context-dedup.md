---
tags: [chore]
---

# Reviewer Phase 1 Context Loading Deduplication

## Problem

spec-reviewer, plan-reviewer, and impl-reviewer each contain an identical Phase 1 block
(~270 words) for context loading (fast-path + disk fallback + ADR summary gate). This was
intentionally inlined per ADR-054 to avoid a network hop, but the implementation is now
copy-pasted verbatim. The `reviewer-context` skill (213 words) exists in the codebase but
is never invoked — making it dead code.

## Motivation

Compressing Phase 1 in all three reviewers to a 4-line summary (fast-path + fallback
protocol key steps) saves ~400 words and eliminates maintenance burden — currently any
protocol change must be applied 3 times. Deleting the unused reviewer-context skill removes
213 words of dead code. Combined: ~600 word reduction.

## Rough Scope

- Compress Phase 1 in spec-reviewer, plan-reviewer, impl-reviewer to a concise form:
  fast-path check + "disk fallback: ADR-000-summary.md → decisions/*.md" (1–2 lines each)
- Delete `skills/reviewer-context/SKILL.md` with a note referencing ADR-054 as the
  reason context loading was inlined rather than delegated
- Verify `test_reviewer_context_chain.py` and `test_lean_load_context.py` still pass
  (they check ordering of ADR-000-summary.md vs wildcard, not word count)
