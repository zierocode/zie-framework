---
approved: true
approved_at: 2026-04-04
backlog: zie-framework/backlog/model-fix-effort-medium-to-low.md
---

# Drop /fix Effort medium → low — Implementation Plan

**Goal:** Reduce token cost of `/fix` by changing `effort: medium` → `effort: low` in `commands/fix.md` frontmatter, since systematic debug checklists don't benefit from extended thinking.

**Architecture:** Purely declarative change — update the YAML frontmatter in `commands/fix.md` and update the test expectation that validates model+effort pairing in `test_model_effort_frontmatter.py`. No logic or step changes.

**Tech Stack:** YAML frontmatter, pytest assertions.

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/fix.md` | Change `effort: medium` → `effort: low` in frontmatter |
| Modify | `tests/unit/test_model_effort_frontmatter.py` | Update EXPECTED dict: `"commands/fix.md"` entry from `("sonnet", "medium")` → `("sonnet", "low")` |

---

## Task 1: Update test expectation and fix command frontmatter

<!-- depends_on: none -->

**Acceptance Criteria:**
- `tests/unit/test_model_effort_frontmatter.py` EXPECTED entry for `"commands/fix.md"` reads `("sonnet", "low")`
- `commands/fix.md` frontmatter reads `effort: low`
- `make test-unit` passes with no regressions
- No changes to `/fix` checklist steps or logic

**Files:**
- Modify: `tests/unit/test_model_effort_frontmatter.py`
- Modify: `commands/fix.md`

- [ ] **Step 1: Write failing tests (RED)**

  Update `tests/unit/test_model_effort_frontmatter.py` EXPECTED dict from:
  ```python
  "commands/fix.md":       ("sonnet", "medium"),
  ```
  To:
  ```python
  "commands/fix.md":       ("sonnet", "low"),
  ```

  Run to confirm RED (frontmatter still has `medium`):
  ```bash
  cd /Users/zie/Code/zie-framework && python -m pytest tests/unit/test_model_effort_frontmatter.py::TestExpectedValues::test_correct_effort_values -x 2>&1 | tail -20
  ```

  Expected: test FAILS with `"commands/fix.md": expected effort='low', got 'medium'`

- [ ] **Step 2: Implement (GREEN)**

  Edit `commands/fix.md` frontmatter line 6:

  From:
  ```yaml
  effort: medium
  ```
  To:
  ```yaml
  effort: low
  ```

  Run to confirm GREEN:
  ```bash
  cd /Users/zie/Code/zie-framework && python -m pytest tests/unit/test_model_effort_frontmatter.py -x 2>&1 | tail -10
  ```

  Expected output: `PASSED`

- [ ] **Step 3: Refactor**

  Run full unit suite to verify no regressions:
  ```bash
  cd /Users/zie/Code/zie-framework && make test-unit
  ```

  Expected output: all tests pass, including `test_model_effort_frontmatter.py::TestExpectedValues::test_correct_effort_values`

---

## Notes

- RED step: test expectation updated first, before touching the source file — this ensures test-driven ordering.
- GREEN step: only the `effort:` line in `commands/fix.md` frontmatter changes; no surrounding logic touched.
- This change is purely declarative and does not affect runtime behavior of `/fix`.
- No integration tests needed — effort is read from frontmatter at invocation time by Claude Code, not by any hook or Python code.
