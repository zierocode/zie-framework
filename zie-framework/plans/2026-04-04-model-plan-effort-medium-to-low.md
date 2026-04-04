---
approved: true
approved_at: 2026-04-04
backlog: backlog/model-plan-effort-medium-to-low.md
---

# Drop /plan Effort medium → low — Implementation Plan

**Goal:** Change `commands/plan.md` frontmatter from `effort: medium` to `effort: low` so the thin orchestration thread stops over-allocating resources.
**Architecture:** Single-file frontmatter edit (`commands/plan.md`) plus a registry update in `tests/unit/test_model_effort_frontmatter.py`. The `EXPECTED` map is the authoritative assertion for all command/skill model+effort pairs; both files must change atomically across Task 1 (RED) and Task 2 (GREEN).
**Tech Stack:** Markdown (frontmatter), Python (pytest unit tests)

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/plan.md` | Change `effort: medium` → `effort: low` in YAML frontmatter |
| Modify | `tests/unit/test_model_effort_frontmatter.py` | Update registry entry `("sonnet", "medium")` → `("sonnet", "low")` for `commands/plan.md` |

## Task Sizing

S plan — 2 tasks, one session. Task 1 updates the test registry (RED); Task 2 flips the frontmatter (GREEN). Task 2 depends on Task 1 (overlapping assertion paths).

---

## Task 1: Update test registry to expect effort: low for commands/plan.md

<!-- depends_on: none -->

**Acceptance Criteria:**
- `tests/unit/test_model_effort_frontmatter.py` EXPECTED map shows `("sonnet", "low")` for `commands/plan.md`
- `make test-unit` fails on `test_correct_effort_values` (RED — commands/plan.md still has effort: medium)
- No other registry entries changed

**Files:**
- Modify: `tests/unit/test_model_effort_frontmatter.py`

- [ ] **Step 1: Write failing tests (RED)**

  Edit line 21 of `tests/unit/test_model_effort_frontmatter.py`:
  ```python
  # Before
  "commands/plan.md":      ("sonnet", "medium"),

  # After
  "commands/plan.md":      ("sonnet", "low"),
  ```

  Run: `make test-unit` — must FAIL with:
  ```
  FAILED tests/unit/test_model_effort_frontmatter.py::TestExpectedValues::test_correct_effort_values
  AssertionError: Wrong effort values:
  commands/plan.md: expected effort='low', got 'medium'
  ```

- [ ] **Step 2: Implement (GREEN)**
  No implementation in this task — GREEN comes from Task 2.
  Task is complete when the registry reflects the desired state and the test is RED.

- [ ] **Step 3: Refactor**
  No refactoring needed; this task is purely a test registry update.
  Run: `make test-unit` — still FAIL (expected — Task 2 not yet done)

---

## Task 2: Change commands/plan.md frontmatter effort to low

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `commands/plan.md` frontmatter reads `effort: low`
- `model: sonnet` remains unchanged
- `make test-unit` passes with no errors

**Files:**
- Modify: `commands/plan.md`

- [ ] **Step 1: Write failing tests (RED)**
  Already RED from Task 1. Confirm:
  Run: `make test-unit` — must FAIL on `test_correct_effort_values` for `commands/plan.md`

- [ ] **Step 2: Implement (GREEN)**

  Edit `commands/plan.md` frontmatter (lines 1–7):
  ```markdown
  ---
  description: Plan a backlog item — draft implementation plan, present for approval, move to Ready lane.
  argument-hint: "[slug...] — one or more backlog item slugs (e.g. zie-plan feature-x feature-y)"
  allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill, Agent, TaskCreate
  model: sonnet
  effort: low
  ---
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No refactoring needed; one-line value change.
  Run: `make test-unit` — still PASS
