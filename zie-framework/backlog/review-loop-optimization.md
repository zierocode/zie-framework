# review-loop-optimization

## Problem

The review loops in spec/plan/implement have unnecessary redundancy: (a) reviewer "Max Iterations" error messages say "invoked 3 times" but the Notes say "Max 2 total iterations" — contradiction in spec-reviewer and plan-reviewer, (b) sprint vs manual flow have different retry semantics for the same reviewer, (c) reviewer Phase 3 "file existence" and "ADR conflict" checks are speculative for spec/plan (files expected not to exist yet), (d) context bundle is re-loaded on each reviewer invocation within the same session.

## Motivation

Each unnecessary reviewer invocation costs ~1000-2000 tokens of context. Unifying retry semantics and removing speculative checks reduces review rounds without sacrificing quality.

## Rough Scope

1. **Fix max-iterations contradiction** — Align error messages ("invoked 3 times") with Notes ("Max 2 total iterations") in spec-reviewer and plan-reviewer. Both should say max 2.
2. **Unify sprint vs manual retry** — Sprint's inline reviewer should use the same 2-iteration cap as manual flow (1 initial + 1 confirm pass). Document the cap explicitly.
3. **Remove speculative file-existence check** — In spec-reviewer and plan-reviewer, skip Phase 3 file-existence check for files marked "Create" (they don't exist yet, that's expected). Keep the check only in impl-reviewer.
4. **Pass context_bundle to avoid re-reads** — Ensure the calling command passes `context_bundle` to all reviewer invocations so the reviewer never re-reads ADRs from disk within the same session.