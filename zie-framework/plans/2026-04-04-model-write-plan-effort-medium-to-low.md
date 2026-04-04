---
approved: true
approved_at: 2026-04-04
backlog: backlog/model-write-plan-effort-medium-to-low.md
---

# Drop write-plan Effort: medium → low — Implementation Plan

**Goal:** Change `skills/write-plan/SKILL.md` frontmatter from `effort: medium` to `effort: low` so the write-plan skill stops over-allocating reasoning budget for structured, schema-driven output.
**Architecture:** Two-file atomic change — the skill frontmatter and the authoritative test registry (`EXPECTED` map in `test_model_effort_frontmatter.py`) must stay in sync. Task 1 updates the registry to RED; Task 2 flips the skill frontmatter to GREEN.
**Tech Stack:** Markdown (frontmatter), Python (pytest unit tests)

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/write-plan/SKILL.md` | Change `effort: medium` → `effort: low` in YAML frontmatter |
| Modify | `tests/unit/test_model_effort_frontmatter.py` | Update registry entry `("sonnet", "medium")` → `("sonnet", "low")` for `skills/write-plan/SKILL.md` |

## Task Sizing

S plan — 2 tasks, one session. Task 1 writes the failing test (RED); Task 2 makes the production change (GREEN). Task 2 depends on Task 1 because both touch the same assertion path.

---

## Task 1: Update test registry to expect effort: low for write-plan skill

<!-- depends_on: none -->

**Acceptance Criteria:**
- `tests/unit/test_model_effort_frontmatter.py` EXPECTED map shows `("sonnet", "low")` for `skills/write-plan/SKILL.md`
- `make test-unit` fails on `test_correct_effort_values` (RED — SKILL.md still has effort: medium)
- No other registry entries changed

**Files:**
- Modify: `tests/unit/test_model_effort_frontmatter.py`

- [ ] **Step 1: Write failing tests (RED)**

  Edit line 31 of `tests/unit/test_model_effort_frontmatter.py`:
  ```python
  # Before
  "skills/write-plan/SKILL.md":    ("sonnet", "medium"),

  # After
  "skills/write-plan/SKILL.md":    ("sonnet", "low"),
  ```

  Run: `make test-unit` — must FAIL with:
  ```
  FAILED tests/unit/test_model_effort_frontmatter.py::TestExpectedValues::test_correct_effort_values
  AssertionError: Wrong effort values:
  skills/write-plan/SKILL.md: expected effort='low', got 'medium'
  ```

- [ ] **Step 2: Implement (GREEN)**
  No implementation in this task — GREEN comes from Task 2.
  Task is complete when the registry reflects the desired state and the test is RED.

- [ ] **Step 3: Refactor**
  No refactoring needed; this task is purely a test registry update.
  Run: `make test-unit` — still FAIL (expected — Task 2 not yet done)

---

## Task 2: Change skills/write-plan/SKILL.md frontmatter effort to low

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `skills/write-plan/SKILL.md` frontmatter reads `effort: low`
- `model: sonnet` remains unchanged
- `make test-unit` passes with no errors

**Files:**
- Modify: `skills/write-plan/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**
  Already RED from Task 1. Confirm:
  Run: `make test-unit` — must FAIL on `test_correct_effort_values` for `skills/write-plan/SKILL.md`

- [ ] **Step 2: Implement (GREEN)**

  Edit `skills/write-plan/SKILL.md` frontmatter — change `effort: medium` to `effort: low`:
  ```markdown
  ---
  name: write-plan
  description: Write a detailed implementation plan from an approved spec. Saves to zie-framework/plans/.
  argument-hint: "<slug> [--no-memory]"
  metadata:
    zie_memory_enabled: true
  model: sonnet
  effort: low
  ---
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No refactoring needed; one-line value change.
  Run: `make test-unit` — still PASS
