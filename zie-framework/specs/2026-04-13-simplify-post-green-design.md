---
approved: true
approved_at: 2026-04-13
backlog: backlog/simplify-post-green.md
---

# Wire Simplify Step Conditionally After GREEN Phase in /implement — Design Spec

**Problem:** After the GREEN phase (all tests pass), the implementation may contain leftover TDD scaffolding, duplicated helper code, or verbose logic from the red-green iteration. There is no automated step in the SDLC workflow to catch this before commit. The `code-simplifier:code-simplifier` skill exists in the framework but is never invoked by any workflow.

**Approach:** Add a conditional simplify step to `commands/implement.md` in the REFACTOR phase, after GREEN is confirmed. The step invokes `Skill(code-simplifier:code-simplifier)` only when the line delta for changed files exceeds a threshold (50 lines). This avoids overhead for small patches while capturing real gains on multi-file features.

**Threshold rationale:** 50 lines is a signal for "non-trivial implementation" — small bug fixes rarely benefit from automated simplification, while multi-file features often have leftover scaffolding from TDD cycles.

**Non-goals:** Not invoked for `/hotfix` or `/chore` tracks. Does not block commit if simplifier finds nothing to change.

**Components:**
- Modify: `commands/implement.md` — add "Simplify Pass" step in REFACTOR phase after GREEN; include line-delta check via `git diff --stat HEAD`; conditional skip logic documented inline

**Data Flow (REFACTOR phase):**
1. GREEN confirmed (all tests pass)
2. Run `git diff --stat HEAD` → read the summary line at the bottom, e.g. `3 files changed, 87 insertions(+), 12 deletions(-)` → sum insertions + deletions = total Δ
3. Run `git diff --name-only HEAD` → collect the list of modified files (these are the "recently modified files" for the simplifier)
4. If total Δ > 50 → invoke `Skill(simplify)` passing the list of recently modified files from step 3
5. If Δ ≤ 50 → print `[simplify] skipped (Δ{n} lines < 50 threshold)` and continue
6. Re-run `make test-fast` after simplify pass to confirm no regressions
7. Continue to impl-reviewer

**Acceptance Criteria:**
- AC1: REFACTOR phase in implement.md includes a conditional simplify step after GREEN
- AC2: Step is skipped when total line delta ≤ 50 (with printed reason)
- AC3: Step invokes `Skill(simplify)` when threshold exceeded
- AC4: Tests re-run after simplify to catch regressions
- AC5: Simplify step clearly documented with threshold rationale in the command
