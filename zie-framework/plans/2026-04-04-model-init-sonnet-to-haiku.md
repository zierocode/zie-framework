---
approved: true
approved_at: 2026-04-04
backlog: backlog/model-init-sonnet-to-haiku.md
---

# Downgrade /init Model: sonnet → haiku — Implementation Plan

**Goal:** Change `commands/init.md` frontmatter from `model: sonnet` to `model: haiku` so that the mechanical scaffolding work runs on a cheaper, faster model.
**Architecture:** Single-file frontmatter edit; the test fixture `test_model_effort_frontmatter.py` already owns the model+effort registry for all commands and skills. Both the source file and the registry test must be updated atomically to keep RED→GREEN clean.
**Tech Stack:** Markdown (frontmatter), Python (pytest unit tests)

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/init.md` | Change `model: sonnet` → `model: haiku` in YAML frontmatter |
| Modify | `tests/unit/test_model_effort_frontmatter.py` | Update registry entry `"commands/init.md": ("sonnet", "medium")` → `("haiku", "medium")` |

## Task Sizing

This is an **S plan** — 2 tasks, both in one session. Task 1 updates the test registry (RED); Task 2 flips the frontmatter (GREEN). Task 2 depends on Task 1 because they both write to overlapping assertion paths.

---

## Task 1: Update test registry to expect haiku for init

<!-- depends_on: none -->

**Acceptance Criteria:**
- `test_model_effort_frontmatter.py` EXPECTED map shows `("haiku", "medium")` for `commands/init.md`
- Running `make test-unit` produces a failure on `test_correct_model_values` (RED — commands/init.md still says sonnet)
- `EXPECTED_HAIKU` list remains unchanged (init is haiku+medium, not haiku+low)

**Files:**
- Modify: `tests/unit/test_model_effort_frontmatter.py`

- [ ] **Step 1: Write failing tests (RED)**

  Edit line 27 of `tests/unit/test_model_effort_frontmatter.py`:
  ```python
  # Before
  "commands/init.md":      ("sonnet", "medium"),

  # After
  "commands/init.md":      ("haiku", "medium"),
  ```

  **Do NOT add init to `EXPECTED_HAIKU` list** — that list is for haiku+low tasks only (see line 172 test). Init is haiku+medium, so it stays in EXPECTED registry only.

  Run: `make test-unit` — must FAIL with:
  ```
  FAILED tests/unit/test_model_effort_frontmatter.py::TestExpectedValues::test_correct_model_values
  AssertionError: Wrong model values:
  commands/init.md: expected model='haiku', got 'sonnet'
  ```

- [ ] **Step 2: Implement (GREEN)**
  No implementation in this task — GREEN comes from Task 2.
  This task is complete when the test registry reflects the desired state and the test is RED.

- [ ] **Step 3: Refactor**
  No refactoring needed; this task is purely a test registry update.

---

## Task 2: Change commands/init.md frontmatter model to haiku

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `commands/init.md` frontmatter reads `model: haiku`
- `effort: medium` remains unchanged
- All existing `test_commands_zie_init.py` tests still pass (pipeline summary, stages, etc.)
- `make test-unit` passes with no errors

**Files:**
- Modify: `commands/init.md`

- [ ] **Step 1: Write failing tests (RED)**
  Already RED from Task 1. Confirm by running: `make test-unit`
  Expected failure: `test_correct_model_values` for `commands/init.md`.

- [ ] **Step 2: Implement (GREEN)**

  Edit `commands/init.md` frontmatter (lines 1–7):
  ```markdown
  ---
  description: Initialize zie-framework in the current project. Run once per project to create SDLC structure, ROADMAP, Makefile, and VERSION.
  argument-hint: (no arguments needed)
  allowed-tools: Read, Write, Bash, Glob, Grep, Agent
  model: haiku
  effort: medium
  ---
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No refactoring needed; this is a one-line value change.
  Run: `make test-unit` — still PASS
