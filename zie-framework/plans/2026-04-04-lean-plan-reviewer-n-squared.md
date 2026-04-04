---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-plan-reviewer-n-squared.md
---

# Lean Plan-Reviewer N² → O(N) File-Map — Implementation Plan

**Goal:** Replace the quadratic pair-check in plan-reviewer Step 10 with an O(N) file-map heuristic that detects all file conflicts in a single linear pass.

**Architecture:** `skills/plan-reviewer/SKILL.md` Step 10 prose is replaced with a two-phase file-map algorithm: build `file → [task IDs]` map in one scan, then flag conflicts from the map. Tests in `tests/unit/test_plan_reviewer_dependency_hints.py` are updated to assert the new prose.

**Tech Stack:** Markdown (skill prose), Python (test assertions via `Path.read_text()`), pytest

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/plan-reviewer/SKILL.md` | Replace Step 10 pair-check with file-map heuristic |
| Modify | `tests/unit/test_plan_reviewer_dependency_hints.py` | Assert new file-map prose; update obsolete pair-check assertions |

---

## Task 1: Rewrite Step 10 in plan-reviewer/SKILL.md with file-map heuristic

**Acceptance Criteria:**
- Step 10 no longer instructs "for each pair of tasks, check whether…"
- Step 10 instructs: build a `file → tasks` map, then flag any file appearing in 2+ tasks
- File conflict blocking-issue wording is preserved
- Advisory suggestion wording ("Tasks N and M appear independent…") is preserved
- `make test-unit` passes (existing tests that check the suggestion format still pass)

**Files:**
- Modify: `skills/plan-reviewer/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**

  Update `tests/unit/test_plan_reviewer_dependency_hints.py` to assert the new file-map prose is present and the old pair-check prose is absent:

  ```python
  def test_file_map_heuristic_present(self):
      text = SKILL_FILE.read_text()
      assert "file → tasks" in text or "file→tasks" in text or \
             "file → [task" in text or "file-map" in text.lower(), \
          "Step 10 must describe the file-map heuristic"

  def test_pair_check_removed(self):
      text = SKILL_FILE.read_text()
      assert "for each pair" not in text.lower(), \
          "Step 10 must not instruct pair-wise checking"
  ```

  Run: `make test-unit` — `test_pair_check_removed` must FAIL (old prose still present), `test_file_map_heuristic_present` must FAIL (new prose absent)

- [ ] **Step 2: Implement (GREEN)**

  Replace Step 10 in `skills/plan-reviewer/SKILL.md`:

  **Remove** (current Step 10):
  ```markdown
  10. **Dependency hints** — For each pair of tasks, check whether they modify
     any common files or share a sequential data dependency. If a pair has
     neither, and neither task has a `depends_on` annotation, output a
     suggestion (not a blocking issue):
     "Tasks N and M appear independent — consider adding `<!-- depends_on: -->` to enable parallel execution"

     **File conflict detection:** If two tasks write to the same output file
     but lack `depends_on` annotation, flag as a blocking issue:
     "Tasks N and M both write to X.py — add `<!-- depends_on: TN -->` to prevent file conflict"

     Suggestions do not prevent an APPROVED verdict, but file conflict warnings do.
  ```

  **Replace with:**
  ```markdown
  10. **Dependency hints** — Build a file→tasks map: for each task, collect all
     file paths it creates or modifies; record `file → [task IDs]`. Then:

     - **File conflict (blocking):** Any file appearing in 2+ task IDs without a
       `depends_on` annotation connecting those tasks → flag as a blocking issue:
       "Tasks N and M both write to X.py — add `<!-- depends_on: TN -->` to prevent file conflict"
     - **Independent tasks (advisory):** Any task with no shared files and no
       `depends_on` annotation → output a suggestion (not a blocking issue):
       "Tasks N and M appear independent — consider adding `<!-- depends_on: -->` to enable parallel execution"

     Skip this check when the plan has 0 or 1 tasks. File conflict warnings
     block APPROVED; suggestions do not.
  ```

  Run: `make test-unit` — all tests must PASS

- [ ] **Step 3: Refactor**

  Verify no trailing whitespace was introduced. Confirm the two new test functions have clear docstrings if the test class lacks them. No logic changes needed.

  Run: `make test-unit` — still PASS

---

## Task 2: Verify integration — 10-task plan conflict detection

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- A synthetic 10-task plan with one shared file and no `depends_on` is flagged as a conflict in the assertion test
- No regressions in existing plan-reviewer test files

**Files:**
- Modify: `tests/unit/test_plan_reviewer_dependency_hints.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add a structural test asserting the new Step 10 describes a map-build step before flagging:

  ```python
  def test_step10_map_build_before_flag(self):
      text = SKILL_FILE.read_text()
      step10_idx = text.find("**Dependency hints**")
      assert step10_idx != -1, "Step 10 header must exist"
      step10_text = text[step10_idx:step10_idx + 600]
      map_mention = "file→tasks" in step10_text or "file → tasks" in step10_text \
                    or "file → [task" in step10_text
      flag_mention = "blocking" in step10_text
      assert map_mention, "Step 10 must describe building a file→tasks map"
      assert flag_mention, "Step 10 must describe flagging conflicts as blocking"
  ```

  Run: `make test-unit` — `test_step10_map_build_before_flag` must FAIL (Task 1 not done yet if run independently; or PASS if Task 1 already complete — acceptable)

- [ ] **Step 2: Implement (GREEN)**

  No additional implementation needed beyond Task 1. The new test validates the prose structure. Run:

  Run: `make test-unit` — all tests must PASS

- [ ] **Step 3: Refactor**

  Confirm `test_plan_reviewer_dependency_hints.py` has consistent test naming and no duplicated assertions between Task 1 and Task 2 additions.

  Run: `make test-unit` — still PASS
