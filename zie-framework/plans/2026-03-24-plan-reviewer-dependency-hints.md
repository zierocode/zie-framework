---
approved: false
approved_at: ~
backlog: backlog/plan-reviewer-dependency-hints.md
spec: specs/2026-03-24-plan-reviewer-dependency-hints-design.md
---

# plan-reviewer Dependency Hints — Implementation Plan

**Goal:** Extend `plan-reviewer` Phase 2 with a dependency scan that identifies task pairs with no shared file modifications and no sequential data dependency, then surfaces them as suggestions (not errors) with a specific output format so developers can unlock parallel execution in `/zie-implement`.
**Architecture:** Single markdown file edit — add item 10 to the Phase 2 checklist in `skills/plan-reviewer/SKILL.md`. No Python, no hooks, no new files. The reviewer's behaviour changes purely through prompt content.
**Tech Stack:** Markdown (skill definition), pytest (file content assertion)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/plan-reviewer/SKILL.md` | Add Phase 2 item 10: dependency scan with suggestion output format |
| Create | `tests/unit/test_plan_reviewer_dependency_hints.py` | Assert new checklist item text is present in the skill file |

---

## Task 1: Add dependency scan item to Phase 2 of `skills/plan-reviewer/SKILL.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- Phase 2 of `skills/plan-reviewer/SKILL.md` contains a new item 10 covering dependency scan
- The suggestion output format in the item reads exactly: `Tasks N and M appear independent — consider adding <!-- depends_on: --> to enable parallel execution`
- The item is advisory — it must not cause `Issues Found` to be raised
- Existing items 1–9 and all other sections are unchanged

**Files:**
- Modify: `skills/plan-reviewer/SKILL.md`
- Create: `tests/unit/test_plan_reviewer_dependency_hints.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_plan_reviewer_dependency_hints.py
  from pathlib import Path

  SKILL_FILE = Path(__file__).parents[2] / "skills" / "plan-reviewer" / "SKILL.md"


  class TestPlanReviewerDependencyHints:
      def test_skill_file_exists(self):
          assert SKILL_FILE.exists()

      def test_dependency_scan_item_present(self):
          text = SKILL_FILE.read_text()
          assert "**Dependency hints**" in text, \
              "Phase 2 must contain a Dependency hints item"

      def test_suggestion_output_format_exact(self):
          text = SKILL_FILE.read_text()
          assert (
              "Tasks N and M appear independent — consider adding "
              "`<!-- depends_on: -->` to enable parallel execution"
          ) in text, \
              "Suggestion output format does not match required exact text"

      def test_item_is_advisory_not_blocking(self):
          text = SKILL_FILE.read_text()
          assert "suggestion" in text.lower(), \
              "Dependency hints item must be labelled as a suggestion (not an error)"

      def test_existing_items_intact(self):
          text = SKILL_FILE.read_text()
          # Spot-check three original Phase 2 items by their headings
          assert "**Header**" in text
          assert "**TDD structure**" in text
          assert "**YAGNI**" in text
  ```
  Run: `make test-unit` — must FAIL (`**Dependency hints**` not yet in file)

- [ ] **Step 2: Implement (GREEN)**

  In `skills/plan-reviewer/SKILL.md`, append item 10 to the Phase 2 checklist
  immediately after item 9 (`**YAGNI**`):

  Before (end of Phase 2 list):
  ```
  9. **YAGNI** — Does the plan include anything the spec doesn't require?
  ```

  After:
  ```
  9. **YAGNI** — Does the plan include anything the spec doesn't require?
  10. **Dependency hints** — For each pair of tasks, check whether they modify
     any common files or share a sequential data dependency. If a pair has
     neither, and neither task has a `depends_on` annotation, output a
     suggestion (not a blocking issue):
     "Tasks N and M appear independent — consider adding
     `<!-- depends_on: -->` to enable parallel execution"
     Suggestions do not prevent an APPROVED verdict.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read the full Phase 2 section of `skills/plan-reviewer/SKILL.md` and confirm:
  - Items 1–9 are byte-for-byte identical to the pre-change file
  - Item 10 is the only addition
  - No trailing whitespace or formatting anomalies introduced
  - The suggestion line contains the exact required string:
    `Tasks N and M appear independent — consider adding <!-- depends_on: --> to enable parallel execution`

  Run: `make test-unit` — still PASS

---

*Commit: `git add skills/plan-reviewer/SKILL.md tests/unit/test_plan_reviewer_dependency_hints.py && git commit -m "feat: plan-reviewer dependency hints"`*
