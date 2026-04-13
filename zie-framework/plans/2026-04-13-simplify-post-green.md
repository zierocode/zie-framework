---
approved: true
approved_at: 2026-04-13
backlog: backlog/simplify-post-green.md
spec: specs/2026-04-13-simplify-post-green-design.md
---

# Wire Simplify Step in /implement — Implementation Plan

**Goal:** Add a conditional `Skill(code-simplifier:code-simplifier)` invocation to `commands/implement.md` in the REFACTOR phase, triggered only when total line delta > 50.

**Tech Stack:** Markdown edit to `commands/implement.md` only. No Python changes.

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `commands/implement.md` | Add simplify step in REFACTOR phase |
| Create | `tests/unit/test_implement_command.py` | New test file verifying simplify step exists and is conditional |

---

## Task 1 — Add simplify step to REFACTOR phase in implement.md

**RED:** Create `tests/unit/test_implement_command.py` with:
```python
def test_simplify_step_present():
    text = (REPO_ROOT / "commands/implement.md").read_text()
    assert "code-simplifier" in text
    assert "simplify" in text.lower()

def test_simplify_threshold_documented():
    text = (REPO_ROOT / "commands/implement.md").read_text()
    assert "50" in text  # threshold

def test_simplify_is_conditional():
    text = (REPO_ROOT / "commands/implement.md").read_text()
    assert "skipped" in text.lower()
```
Run `make test-fast` → confirm these 3 tests FAIL (implement.md doesn't have simplify yet).

**GREEN:** In `commands/implement.md`, insert the following block into the REFACTOR phase, immediately after "GREEN confirmed" and before invoking impl-reviewer:

```markdown
**Simplify pass (conditional):**
1. Run `git diff --stat HEAD` → read the summary line, e.g. `3 files changed, 87 insertions(+), 12 deletions(-)` → sum insertions + deletions = total Δ
2. Run `git diff --name-only HEAD` → collect recently modified files list
3. If total Δ > 50 → invoke `Skill(code-simplifier:code-simplifier)` on the recently modified files list
4. If Δ ≤ 50 → print `[simplify] skipped (Δ{n} lines < 50 threshold)` and continue
5. After simplify (if run) → re-run `make test-fast` to confirm no regressions introduced
```

**Acceptance Criteria:**
- [ ] REFACTOR phase has conditional simplify step
- [ ] Both branches (>50 and ≤50) are explicitly documented
- [ ] `make test-fast` re-run after simplify is specified
- [ ] Step is placed BEFORE impl-reviewer invocation

---

## Task 2 — Verify GREEN and run full suite

**GREEN verification:** Run `make test-fast` → all 3 tests from Task 1 RED now pass.

**REFACTOR:** Run `make test-unit` → full suite passes (no regressions). If any tests fail, stop and fix before proceeding.

**Acceptance Criteria:**
- [ ] 3 tests that were RED in Task 1 are now GREEN
- [ ] Existing implement command tests still pass
- [ ] Full test suite stays green

---

## Estimated Risk: LOW
- Pure markdown edit, no code changes
- Additive step; existing REFACTOR flow unchanged otherwise
- Tests verify structural presence, not runtime behavior
