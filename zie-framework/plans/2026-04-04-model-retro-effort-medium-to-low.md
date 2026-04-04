---
approved: true
approved_at: 2026-04-04
backlog: backlog/model-retro-effort-medium-to-low.md
---

# Drop /retro effort: medium → low — Implementation Plan

**Goal:** Reduce `/retro` effort from `medium` to `low` to cut token cost on structured template-filling work.
**Architecture:** One-line frontmatter change in the command file; one-line tuple update in the test EXPECTED map. No logic change — effort is a model hint only.
**Tech Stack:** Markdown frontmatter (YAML), pytest

---

## Execution Order

TDD discipline requires the failing test to exist before the fix is applied:

1. **Task 1 (RED):** Update `EXPECTED` map in the test → test fails (file still says `medium`)
2. **Task 2 (GREEN):** Update `commands/retro.md` frontmatter → test passes

Task 2 depends on Task 1.

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `tests/unit/test_model_effort_frontmatter.py` | Update `EXPECTED["commands/retro.md"]` tuple to `("sonnet", "low")` — creates the failing test |
| Modify | `commands/retro.md` | Change `effort: medium` → `effort: low` in frontmatter — makes the test pass |

---

## Task 1: Update `EXPECTED` map in test (RED)

<!-- depends_on: none -->

**Acceptance Criteria:**
- `EXPECTED["commands/retro.md"]` is `("sonnet", "low")`
- `make test-unit` FAILS after this task alone (source file unchanged)

**Files:**
- Modify: `tests/unit/test_model_effort_frontmatter.py`

- [ ] **Step 1: Write failing test (RED)**

  Change the tuple in `EXPECTED`:
  ```python
  "commands/retro.md":     ("sonnet", "low"),   # was ("sonnet", "medium")
  ```

  Run: `make test-unit`
  Expected result: `TestExpectedValues::test_correct_effort_values` FAILS.
  Reason: EXPECTED says `low`, but `commands/retro.md` still contains `effort: medium`.
  This is the correct RED state — the test is live and sensitive to the frontmatter value.

- [ ] **Step 2: Implement**

  No further code change in this task — the EXPECTED map update IS the implementation for Task 1.

- [ ] **Step 3: Refactor**

  No refactor needed.

---

## Task 2: Update `commands/retro.md` frontmatter (GREEN)

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `commands/retro.md` frontmatter contains `effort: low`
- `commands/retro.md` frontmatter still contains `model: sonnet`
- `make test-unit` PASSES with both Task 1 and Task 2 applied

**Files:**
- Modify: `commands/retro.md`

**Pre-condition:** Task 1 must already be applied. The test suite must currently be in RED state (EXPECTED map updated, source file still `medium`).

- [ ] **Step 1: Confirm RED (no code change)**

  Run: `make test-unit`
  Expected: `test_correct_effort_values` FAILS — confirms RED state from Task 1.

- [ ] **Step 2: Implement (GREEN)**

  In `commands/retro.md`, change the frontmatter line:
  ```yaml
  effort: medium
  ```
  to:
  ```yaml
  effort: low
  ```

  Run: `make test-unit` — `test_correct_effort_values` must PASS.
  Both changes are now in place: EXPECTED map says `low`, source file says `low`.

- [ ] **Step 3: Refactor**

  No refactor needed — single-line change.
  Run: `make test-unit` — still PASS

---

## Verification

```bash
make test-ci
```

Expected: all tests green, coverage gate passes. No new tests required beyond the updated assertion.
