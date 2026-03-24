---
approved: false
approved_at: ~
backlog: backlog/reviewer-terse-output.md
spec: specs/2026-03-24-reviewer-terse-output-design.md
---

# Reviewer Terse Output — Implementation Plan

**Goal:** Replace verbose output sections in all three reviewer skills with a strict terse format: approval = exactly `✅ APPROVED` (one line, nothing else); issues = `❌ Issues Found` header + numbered bullets only.
**Architecture:** Pure content edit — three SKILL.md files. The Output Format section in each skill is replaced in-place. No logic changes, no new files, no caller changes.
**Tech Stack:** Markdown (skill definitions), pytest (Path.read_text() pattern assertions)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/spec-reviewer/SKILL.md` | Replace Output Format section with terse spec |
| Modify | `skills/plan-reviewer/SKILL.md` | Replace Output Format section with terse spec |
| Modify | `skills/impl-reviewer/SKILL.md` | Replace Output Format section with terse spec |
| Create | `tests/unit/test_reviewer_terse_output.py` | Assert terse format present; assert verbose prose absent |

---

## Task 1: Terse output for `skills/spec-reviewer/SKILL.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `skills/spec-reviewer/SKILL.md` Output Format section contains exactly `✅ APPROVED` as the sole approval output (no second line)
- Approval block contains no prose sentence (e.g. "Spec is complete..." must be absent)
- Issues block starts with `❌ Issues Found` followed immediately by a numbered list
- No prose introduction before the numbered list
- No multi-sentence closing instruction (single-line fix prompt only)
- Phase 1, Phase 2, Phase 3 content is unchanged

**Files:**
- Modify: `skills/spec-reviewer/SKILL.md`
- Create: `tests/unit/test_reviewer_terse_output.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_reviewer_terse_output.py
  from pathlib import Path

  SKILLS_DIR = Path(__file__).parents[2] / "skills"


  class TestSpecReviewerTerseOutput:
      def _text(self) -> str:
          return (SKILLS_DIR / "spec-reviewer" / "SKILL.md").read_text()

      def test_approval_line_is_exactly_approved(self):
          text = self._text()
          assert "✅ APPROVED\n```" in text, \
              "Approval block must end immediately after '✅ APPROVED' with no extra lines"

      def test_no_verbose_approval_prose(self):
          text = self._text()
          assert "Spec is complete, clear, and scoped correctly." not in text, \
              "Verbose approval prose must be removed"

      def test_issues_header_present(self):
          text = self._text()
          assert "❌ Issues Found" in text

      def test_no_prose_before_bullets(self):
          text = self._text()
          # The issues block must go straight from header to numbered list
          assert "❌ Issues Found\n\n1." in text, \
              "Issues block must have no prose between header and first bullet"

      def test_single_line_fix_prompt(self):
          text = self._text()
          assert "Fix these and re-submit for review." in text

      def test_phase_headings_unchanged(self):
          text = self._text()
          assert "## Phase 1" in text
          assert "## Phase 2" in text
          assert "## Phase 3" in text
  ```

  Run: `make test-unit` — must FAIL (`"Spec is complete, clear, and scoped correctly."` still present)

- [ ] **Step 2: Implement (GREEN)**

  In `skills/spec-reviewer/SKILL.md`, replace the entire `## Output Format` section.

  Before:
  ```
  ## Output Format

  If all checks pass:

  ```text
  ✅ APPROVED

  Spec is complete, clear, and scoped correctly.
  ```

  If issues found:

  ```text
  ❌ Issues Found

  1. [Section] <specific issue and what to fix>
  2. [Section] <specific issue and what to fix>

  Fix these and re-submit for review.
  ```
  ```

  After:
  ```
  ## Output Format

  If all checks pass:

  ```text
  ✅ APPROVED
  ```

  If issues found:

  ```text
  ❌ Issues Found

  1. [Section] <specific issue and what to fix>
  2. [Section] <specific issue and what to fix>

  Fix these and re-submit for review.
  ```
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read `skills/spec-reviewer/SKILL.md` in full. Confirm Phase 1, Phase 2, Phase 3,
  and Notes sections are byte-for-byte unchanged. Confirm no trailing blank lines
  were introduced inside the approval code fence.
  Run: `make test-unit` — still PASS

---

## Task 2: Terse output for `skills/plan-reviewer/SKILL.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `skills/plan-reviewer/SKILL.md` Output Format section contains exactly `✅ APPROVED` as the sole approval output
- Approval block contains no prose sentence (e.g. "Plan is complete..." must be absent)
- Issues block starts with `❌ Issues Found` followed immediately by a numbered list
- No prose introduction before the numbered list
- Single-line fix prompt only
- Phase 1, Phase 2, Phase 3 content is unchanged

**Files:**
- Modify: `skills/plan-reviewer/SKILL.md`
- Modify: `tests/unit/test_reviewer_terse_output.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_reviewer_terse_output.py — add after TestSpecReviewerTerseOutput

  class TestPlanReviewerTerseOutput:
      def _text(self) -> str:
          return (SKILLS_DIR / "plan-reviewer" / "SKILL.md").read_text()

      def test_approval_line_is_exactly_approved(self):
          text = self._text()
          assert "✅ APPROVED\n```" in text, \
              "Approval block must end immediately after '✅ APPROVED' with no extra lines"

      def test_no_verbose_approval_prose(self):
          text = self._text()
          assert "Plan is complete, TDD-structured, and covers the spec." not in text, \
              "Verbose approval prose must be removed"

      def test_issues_header_present(self):
          text = self._text()
          assert "❌ Issues Found" in text

      def test_no_prose_before_bullets(self):
          text = self._text()
          assert "❌ Issues Found\n\n1." in text, \
              "Issues block must have no prose between header and first bullet"

      def test_single_line_fix_prompt(self):
          text = self._text()
          assert "Fix these and re-submit for review." in text

      def test_phase_headings_unchanged(self):
          text = self._text()
          assert "## Phase 1" in text
          assert "## Phase 2" in text
          assert "## Phase 3" in text
  ```

  Run: `make test-unit` — must FAIL (`"Plan is complete, TDD-structured, and covers the spec."` still present)

- [ ] **Step 2: Implement (GREEN)**

  In `skills/plan-reviewer/SKILL.md`, replace the entire `## Output Format` section.

  Before:
  ```
  ## Output Format

  If all checks pass:

  ```text
  ✅ APPROVED

  Plan is complete, TDD-structured, and covers the spec.
  ```

  If issues found:

  ```text
  ❌ Issues Found

  1. [Task N / Section] <specific issue and what to fix>
  2. [Task N / Section] <specific issue and what to fix>

  Fix these and re-submit for review.
  ```
  ```

  After:
  ```
  ## Output Format

  If all checks pass:

  ```text
  ✅ APPROVED
  ```

  If issues found:

  ```text
  ❌ Issues Found

  1. [Task N / Section] <specific issue and what to fix>
  2. [Task N / Section] <specific issue and what to fix>

  Fix these and re-submit for review.
  ```
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read `skills/plan-reviewer/SKILL.md` in full. Confirm Phase 1, Phase 2, Phase 3,
  and Notes sections are unchanged. Confirm the bullet placeholder text
  `[Task N / Section]` is preserved exactly (not simplified to `[Section]`).
  Run: `make test-unit` — still PASS

---

## Task 3: Terse output for `skills/impl-reviewer/SKILL.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `skills/impl-reviewer/SKILL.md` Output Format section contains exactly `✅ APPROVED` as the sole approval output
- Approval block contains no prose sentence (e.g. "Implementation satisfies AC..." must be absent)
- Issues block starts with `❌ Issues Found` followed immediately by a numbered list
- No prose introduction before the numbered list
- Single-line fix prompt only (the existing one-line prompt is preserved)
- Phase 1, Phase 2, Phase 3 content is unchanged

**Files:**
- Modify: `skills/impl-reviewer/SKILL.md`
- Modify: `tests/unit/test_reviewer_terse_output.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_reviewer_terse_output.py — add after TestPlanReviewerTerseOutput

  class TestImplReviewerTerseOutput:
      def _text(self) -> str:
          return (SKILLS_DIR / "impl-reviewer" / "SKILL.md").read_text()

      def test_approval_line_is_exactly_approved(self):
          text = self._text()
          assert "✅ APPROVED\n```" in text, \
              "Approval block must end immediately after '✅ APPROVED' with no extra lines"

      def test_no_verbose_approval_prose(self):
          text = self._text()
          assert "Implementation satisfies AC. Tests present and passing." not in text, \
              "Verbose approval prose must be removed"

      def test_issues_header_present(self):
          text = self._text()
          assert "❌ Issues Found" in text

      def test_no_prose_before_bullets(self):
          text = self._text()
          assert "❌ Issues Found\n\n1." in text, \
              "Issues block must have no prose between header and first bullet"

      def test_single_line_fix_prompt(self):
          text = self._text()
          assert "Fix these, re-run make test-unit, and re-invoke impl-reviewer." in text

      def test_phase_headings_unchanged(self):
          text = self._text()
          assert "## Phase 1" in text
          assert "## Phase 2" in text
          assert "## Phase 3" in text
  ```

  Run: `make test-unit` — must FAIL (`"Implementation satisfies AC. Tests present and passing."` still present)

- [ ] **Step 2: Implement (GREEN)**

  In `skills/impl-reviewer/SKILL.md`, replace the entire `## Output Format` section.

  Before:
  ```
  ## Output Format

  If all checks pass:

  ```text
  ✅ APPROVED

  Implementation satisfies AC. Tests present and passing.
  ```

  If issues found:

  ```text
  ❌ Issues Found

  1. [File:line] <specific issue and what to fix>
  2. [File:line] <specific issue and what to fix>

  Fix these, re-run make test-unit, and re-invoke impl-reviewer.
  ```
  ```

  After:
  ```
  ## Output Format

  If all checks pass:

  ```text
  ✅ APPROVED
  ```

  If issues found:

  ```text
  ❌ Issues Found

  1. [File:line] <specific issue and what to fix>
  2. [File:line] <specific issue and what to fix>

  Fix these, re-run make test-unit, and re-invoke impl-reviewer.
  ```
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read `skills/impl-reviewer/SKILL.md` in full. Confirm Phase 1, Phase 2, Phase 3,
  and Notes sections are unchanged. Confirm the bullet placeholder text `[File:line]`
  is preserved exactly.
  Run: `make test-unit` — still PASS

---

*Commit: `git add skills/spec-reviewer/SKILL.md skills/plan-reviewer/SKILL.md skills/impl-reviewer/SKILL.md tests/unit/test_reviewer_terse_output.py && git commit -m "feat: reviewer-terse-output"`*
