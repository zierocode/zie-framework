---
approved: true
approved_at: 2026-03-24
backlog: backlog/verify-scoped-mode.md
---

# verify Skill Scoped Mode — Design Spec

**Problem:** The `verify` skill runs all 5 checks (tests, regressions, TODOs, code review, docs sync) regardless of caller context. `/zie-fix` calls it with "scope = tests only" intent but the skill ignores scope — bug fixes get a full docs sync and code review they don't need.

**Approach:** Add a `scope` parameter to the verify skill. `scope=full` (default) runs all 5 checks as today. `scope=tests-only` runs checks 1 (tests pass), 2 (no regressions), and a partial check 4 (secrets scan only — no full code review). Update `/zie-fix` to explicitly pass `scope=tests-only`.

**Components:**
- Modify: `skills/verify/SKILL.md` — add `scope` parameter to invocation interface; add conditional block: if `tests-only`, skip docs sync (check 5) and full code review portion of check 4; secrets scan in check 4 always runs
- Modify: `commands/zie-fix.md` — pass `scope=tests-only` to `Skill(zie-framework:verify)` invocation

**Acceptance Criteria:**
- [ ] `scope=tests-only` runs: tests (1), no regressions (2), secrets scan only from (4)
- [ ] `scope=tests-only` skips: docs sync (5) and full code review portion of (4)
- [ ] `scope=full` runs all 5 checks — behavior identical to today
- [ ] `/zie-fix` passes `scope=tests-only` by default
- [ ] Default scope is `full` when caller does not specify
- [ ] No other callers of verify are changed

**Out of Scope:**
- Adding additional scope modes beyond `full` and `tests-only`
- Changing what `scope=full` checks
