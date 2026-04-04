---
approved: true
approved_at: 2026-04-04
backlog: zie-framework/backlog/model-debug-effort-medium-to-low.md
---

# Drop Debug Skill Effort medium → low — Implementation Plan

**Goal:** Reduce token cost of debug skill by changing `effort: medium` → `effort: low`, since structured debugging checklists don't benefit from extended thinking.

**Architecture:** The change is purely declarative — update the YAML frontmatter in the debug skill file and update the test expectation that validates model+effort pairing. No logic changes.

**Tech Stack:** YAML frontmatter parsing, pytest assertions.

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/debug/SKILL.md` | Change `effort: medium` → `effort: low` in frontmatter |
| Modify | `tests/unit/test_model_effort_frontmatter.py` | Update EXPECTED dict: line 32 from `("sonnet", "medium")` → `("sonnet", "low")` |

---

## Task 1: Update debug skill frontmatter

<!-- depends_on: none -->

**Acceptance Criteria:**
- `skills/debug/SKILL.md` line 9 reads `effort: low` (not `medium`)
- `make test-unit` passes (including effort frontmatter test)
- No changes to skill description or steps

**Files:**
- Modify: `skills/debug/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**

  Current test expects `effort: medium`. Run:
  ```bash
  cd /Users/zie/Code/zie-framework && make test-unit -k "test_correct_effort_values"
  ```

  Expected output includes failure:
  ```
  skills/debug/SKILL.md: expected effort='low', got 'medium'
  ```

- [ ] **Step 2: Implement (GREEN)**

  Edit `skills/debug/SKILL.md` line 9:
  ```yaml
  ---
  name: debug
  description: Systematic debugging — reproduce, isolate, fix, verify. Uses zie-memory to surface known failure patterns.
  metadata:
    zie_memory_enabled: true
  user-invocable: false
  argument-hint: ""
  model: sonnet
  effort: low
  ---
  ```

  Run:
  ```bash
  cd /Users/zie/Code/zie-framework && make test-unit -k "test_correct_effort_values"
  ```

  Expected output: `PASSED`

- [ ] **Step 3: Refactor**

  Verify full suite still passes:
  ```bash
  cd /Users/zie/Code/zie-framework && make test-unit
  ```

  Expected output: all tests pass, including `test_model_effort_frontmatter.py::TestExpectedValues::test_correct_effort_values`

---

## Task 2: Update test expectation

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `tests/unit/test_model_effort_frontmatter.py` line 32 reads `("sonnet", "low")` (not `("sonnet", "medium")`)
- `make test-unit` passes
- Test still validates debug skill effort matches frontmatter

**Files:**
- Modify: `tests/unit/test_model_effort_frontmatter.py`

- [ ] **Step 1: Write failing tests (RED)**

  If the test expectation hasn't been updated yet, the test will fail:
  ```bash
  cd /Users/zie/Code/zie-framework && make test-unit -k "test_correct_effort_values"
  ```

  Expected output: failure with message about effort mismatch.

- [ ] **Step 2: Implement (GREEN)**

  Edit `tests/unit/test_model_effort_frontmatter.py` line 32:

  From:
  ```python
  "skills/debug/SKILL.md":         ("sonnet", "medium"),
  ```

  To:
  ```python
  "skills/debug/SKILL.md":         ("sonnet", "low"),
  ```

  Run:
  ```bash
  cd /Users/zie/Code/zie-framework && make test-unit -k "test_correct_effort_values"
  ```

  Expected output: `PASSED`

- [ ] **Step 3: Refactor**

  Run full test suite to verify no regressions:
  ```bash
  cd /Users/zie/Code/zie-framework && make test-unit
  ```

  Expected output: all tests pass, including `test_model_effort_frontmatter.py`

---

## Notes

- Task 1 and Task 2 serialize: Task 1 updates the file, Task 2 updates the test expectation. The test must be updated after the file is changed, or CI will report a failure.
- Both tasks are required for a successful change: the skill file alone is incomplete; the test must also be updated to reflect the new expected value.
- No integration tests needed — this change is purely declarative and doesn't affect runtime behavior.
