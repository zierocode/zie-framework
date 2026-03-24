---
approved: false
approved_at: ~
backlog: backlog/spec-design-batch-approval.md
spec: specs/2026-03-24-spec-design-batch-approval-design.md
---

# spec-design Batch Section Approval — Implementation Plan

**Goal:** Replace the section-by-section approval loop in `spec-design` with a single full-draft presentation — write all sections in one pass, present once for review, apply all edits in one batch if changes are requested, then proceed to spec-reviewer only after the user accepts.

**Architecture:** Single file change — `skills/spec-design/SKILL.md`. Step 3 currently presents each section individually and awaits approval before continuing. The new flow writes all five sections without interruption, presents the complete draft, handles one round of batch edits if needed, then continues to Step 4 (write spec to disk) and beyond. All other steps and section content are unchanged.

**Tech Stack:** Markdown (skill definition), pytest (text assertions on SKILL.md)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/spec-design/SKILL.md` | Replace section-by-section approval loop with single full-draft review prompt |
| Create | `tests/unit/test_spec_design_batch_approval.py` | Assert new approval pattern present, old pattern absent, batch edit language present |

---

## Task 1: Replace section-by-section approval loop with single full-draft review

<!-- depends_on: none -->

**Acceptance Criteria:**
- `skills/spec-design/SKILL.md` does NOT contain the phrase `get approval after each`
- `skills/spec-design/SKILL.md` contains exactly one review prompt after the full draft (matches: `Review the complete draft`)
- `skills/spec-design/SKILL.md` contains batch edit language (matches: `apply all requested changes`)
- All five section names remain present: `Problem & Motivation`, `Architecture & Components`, `Data Flow`, `Edge Cases`, `Out of Scope`
- spec-reviewer invocation is still present and unchanged

**Files:**
- Modify: `skills/spec-design/SKILL.md`
- Create: `tests/unit/test_spec_design_batch_approval.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_spec_design_batch_approval.py
  from pathlib import Path

  SKILL_PATH = Path(__file__).parents[2] / "skills" / "spec-design" / "SKILL.md"


  def skill_text() -> str:
      return SKILL_PATH.read_text()


  class TestBatchApprovalStructure:
      def test_skill_file_exists(self):
          assert SKILL_PATH.exists()

      def test_section_by_section_approval_removed(self):
          assert "get approval after each" not in skill_text(), (
              "section-by-section approval phrase must be removed"
          )

      def test_single_review_prompt_present(self):
          assert "Review the complete draft" in skill_text(), (
              "single full-draft review prompt must be present"
          )

      def test_batch_edit_language_present(self):
          assert "apply all requested changes" in skill_text(), (
              "batch edit language must be present"
          )

      def test_all_sections_still_present(self):
          text = skill_text()
          for section in (
              "Problem & Motivation",
              "Architecture & Components",
              "Data Flow",
              "Edge Cases",
              "Out of Scope",
          ):
              assert section in text, f"section must remain: {section}"

      def test_spec_reviewer_invocation_still_present(self):
          assert "spec-reviewer" in skill_text(), (
              "spec-reviewer invocation must remain intact"
          )
  ```

  Run: `make test-unit` — must FAIL (`get approval after each` still present, `Review the complete draft` absent)

- [ ] **Step 2: Implement (GREEN)**

  In `skills/spec-design/SKILL.md`, replace Step 3 entirely.

  Before:
  ```
  3. **Present design sections** — get approval after each:
     - Problem & Motivation
     - Architecture & Components
     - Data Flow
     - Edge Cases
     - Out of Scope
  ```

  After:
  ```
  3. **Draft all design sections** in one pass — no approval prompts between sections:
     - Problem & Motivation
     - Architecture & Components
     - Data Flow
     - Edge Cases
     - Out of Scope

     Once all sections are written, present the complete draft to the user.

     **Review the complete draft** — ask the user:
     > "Here is the full spec draft. Does this look right, or would you like
     > any changes?"

     If the user requests changes: apply all requested changes to the draft
     in one batch, re-present the updated draft once, then continue.
     If the user accepts: proceed to Step 4.

     Max one re-draft cycle. If further issues remain after one round of
     edits, surface to the user for section-level guidance before continuing.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read the full updated SKILL.md and confirm:
  - Steps 1, 2, 4, 5, 6, 7, 8, 9 are byte-for-byte identical to their pre-change state
  - The spec-reviewer loop at Step 5 is intact (including the fallback comment)
  - No stray approval prompts remain between the five section names

  Run: `make test-unit` — still PASS

---

*Commit: `git add skills/spec-design/SKILL.md tests/unit/test_spec_design_batch_approval.py && git commit -m "feat: spec-design batch section approval"`*
