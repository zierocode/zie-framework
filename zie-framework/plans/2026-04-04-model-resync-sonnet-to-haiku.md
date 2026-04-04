---
approved: true
approved_at: 2026-04-04
backlog: backlog/model-resync-sonnet-to-haiku.md
---

# Downgrade /resync Model: sonnet → haiku — Implementation Plan

**Goal:** Change `commands/resync.md` frontmatter from `model: sonnet` to `model: haiku` so the mechanical coordinator role runs on the cheaper model.
**Architecture:** Single-file frontmatter edit; no logic changes. The EXPECTED map in `test_model_effort_frontmatter.py` must be updated to match the new value so `TestExpectedValues.test_correct_model_values` stays green.
**Tech Stack:** Markdown (frontmatter), Python (pytest test fixture map)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/resync.md` | Change `model: sonnet` → `model: haiku` in frontmatter |
| Modify | `tests/unit/test_model_effort_frontmatter.py` | Update EXPECTED entry for `commands/resync.md` from `("sonnet", "medium")` to `("haiku", "medium")` |

---

## Task 1: Update EXPECTED map in test (RED → GREEN)

**Acceptance Criteria:**
- `TestExpectedValues.test_correct_model_values` passes after both files are changed.
- No other test in `test_model_effort_frontmatter.py` or `test_model_routing_v2.py` fails.

**Files:**
- Modify: `tests/unit/test_model_effort_frontmatter.py`

- [ ] **Step 1: Write failing test baseline (RED)**

  Before touching any production file, run the suite to confirm the current state is green:

  ```bash
  make test-unit 2>&1 | tail -20
  ```

  Expected: all pass (baseline confirmed).

- [ ] **Step 2: Change EXPECTED entry (GREEN setup)**

  In `tests/unit/test_model_effort_frontmatter.py`, line 27, change:

  ```python
  "commands/resync.md":    ("sonnet", "medium"),
  ```

  to:

  ```python
  "commands/resync.md":    ("haiku",  "medium"),
  ```

  Run: `make test-unit` — must **FAIL** on `test_correct_model_values` (actual file still has `sonnet`). This is the RED state confirming the test is load-bearing.

- [ ] **Step 3: Refactor**

  No cleanup needed — single-line change.

---

## Task 2: Change frontmatter in commands/resync.md

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `commands/resync.md` frontmatter contains `model: haiku`.
- `effort: medium` is unchanged.
- `make test-unit` passes fully (GREEN).
- `make lint` passes (no ruff violations introduced).

**Files:**
- Modify: `commands/resync.md`

- [ ] **Step 1: Write failing confirmation (RED)**

  After Task 1 Step 2, the test suite is in RED. This task is the GREEN step.

- [ ] **Step 2: Edit frontmatter (GREEN)**

  In `commands/resync.md`, change line 5 from:

  ```yaml
  model: sonnet
  ```

  to:

  ```yaml
  model: haiku
  ```

  `effort: medium` on line 6 is untouched.

  Run: `make test-unit` — must **PASS**.

  ```bash
  make test-unit 2>&1 | tail -20
  # Expected: all tests pass, no failures
  ```

- [ ] **Step 3: Lint + full gate**

  ```bash
  make lint
  make test-ci 2>&1 | tail -30
  ```

  Both must pass with zero errors before committing.

---

## Completion Checklist

- [ ] Task 1 complete — EXPECTED map updated, RED confirmed
- [ ] Task 2 complete — frontmatter changed, GREEN confirmed
- [ ] `make test-ci` passes
- [ ] `make lint` passes
