---
approved: false
approved_at: ~
backlog: backlog/reviewer-fail-fast.md
spec: specs/2026-03-24-reviewer-fail-fast-design.md
---

# Reviewer Fail-Fast — All Issues in One Pass — Implementation Plan

**Goal:** Eliminate unnecessary reviewer round-trips by (1) instructing all three reviewer skills to return every issue found in a single response, and (2) changing the caller loop in `/zie-plan` and `/zie-implement` from "fix one → re-review" to "initial scan → fix all → one final confirm pass". Max iterations drops from 3-per-issue to 2 total per review cycle.
**Architecture:** Pure Markdown edits — no new files, no new hooks. Three reviewer SKILL.md files get updated output instructions. Two command files get updated iteration logic. Tests use `Path.read_text()` to assert required string patterns are present/absent.
**Tech Stack:** Markdown (skill/command files), pytest (pattern tests)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/spec-reviewer/SKILL.md` | Add "surface ALL issues" instruction; update Notes; remove per-issue max |
| Modify | `skills/plan-reviewer/SKILL.md` | Same changes |
| Modify | `skills/impl-reviewer/SKILL.md` | Same changes |
| Modify | `commands/zie-plan.md` | Replace 3-iteration fix loop with 2-pass pattern (initial scan + confirm) |
| Modify | `commands/zie-implement.md` | Same 2-pass iteration change |
| Create | `tests/unit/test_reviewer_fail_fast.py` | Pattern assertions for all five modified files |

---

## Task 1: Update reviewer output instructions (3 skills)

<!-- depends_on: none -->

**Acceptance Criteria:**
- `skills/spec-reviewer/SKILL.md` contains the phrase `"Return ALL issues found"` in its Output Format section
- `skills/plan-reviewer/SKILL.md` contains the phrase `"Return ALL issues found"` in its Output Format section
- `skills/impl-reviewer/SKILL.md` contains the phrase `"Return ALL issues found"` in its Output Format section
- None of the three files contains `"Max 3 review iterations"` (old cap removed)
- Each file contains `"Max 2 total iterations"` (new cap)
- The `❌ Issues Found` output block in each skill adds a preamble line instructing the reviewer to list every issue before asking for fixes
- Checklist items (Phase 2, Phase 3) are unchanged

**Files:**
- Modify: `skills/spec-reviewer/SKILL.md`
- Modify: `skills/plan-reviewer/SKILL.md`
- Modify: `skills/impl-reviewer/SKILL.md`
- Create: `tests/unit/test_reviewer_fail_fast.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_reviewer_fail_fast.py
  from pathlib import Path

  ROOT = Path(__file__).parents[2]
  SKILLS_DIR = ROOT / "skills"
  COMMANDS_DIR = ROOT / "commands"


  # --- helpers ---

  def skill_text(name: str) -> str:
      return (SKILLS_DIR / name / "SKILL.md").read_text()

  def command_text(name: str) -> str:
      return (COMMANDS_DIR / f"{name}.md").read_text()


  # --- Task 1: reviewer output instructions ---

  class TestReviewerOutputInstructions:
      def test_spec_reviewer_all_issues_instruction(self):
          assert "Return ALL issues found" in skill_text("spec-reviewer"), \
              "spec-reviewer must instruct reviewer to return ALL issues"
          assert "do not stop at the first issue" in skill_text("spec-reviewer"), \
              "spec-reviewer must instruct reviewer not to stop at first issue"

      def test_plan_reviewer_all_issues_instruction(self):
          assert "Return ALL issues found" in skill_text("plan-reviewer"), \
              "plan-reviewer must instruct reviewer to return ALL issues"
          assert "do not stop at the first issue" in skill_text("plan-reviewer"), \
              "plan-reviewer must instruct reviewer not to stop at first issue"

      def test_impl_reviewer_all_issues_instruction(self):
          assert "Return ALL issues found" in skill_text("impl-reviewer"), \
              "impl-reviewer must instruct reviewer to return ALL issues"
          assert "do not stop at the first issue" in skill_text("impl-reviewer"), \
              "impl-reviewer must instruct reviewer not to stop at first issue"

      def test_spec_reviewer_no_old_max(self):
          assert "Max 3 review iterations" not in skill_text("spec-reviewer"), \
              "spec-reviewer must not contain old 3-iteration cap"

      def test_plan_reviewer_no_old_max(self):
          assert "Max 3 review iterations" not in skill_text("plan-reviewer"), \
              "plan-reviewer must not contain old 3-iteration cap"

      def test_impl_reviewer_no_old_max(self):
          assert "Max 3 review iterations" not in skill_text("impl-reviewer"), \
              "impl-reviewer must not contain old 3-iteration cap"

      def test_spec_reviewer_new_max(self):
          assert "Max 2 total iterations" in skill_text("spec-reviewer"), \
              "spec-reviewer must declare Max 2 total iterations"

      def test_plan_reviewer_new_max(self):
          assert "Max 2 total iterations" in skill_text("plan-reviewer"), \
              "plan-reviewer must declare Max 2 total iterations"

      def test_impl_reviewer_new_max(self):
          assert "Max 2 total iterations" in skill_text("impl-reviewer"), \
              "impl-reviewer must declare Max 2 total iterations"
  ```
  Run: `make test-unit` — must FAIL (strings not yet present)

- [ ] **Step 2: Implement (GREEN)**

  **`skills/spec-reviewer/SKILL.md`** — two edits:

  In the `## Output Format` section, replace the `❌ Issues Found` block:

  Before:
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
  If issues found:

  ```text
  ❌ Issues Found

  Return ALL issues found in this single response — do not stop at the first issue.

  1. [Section] <specific issue and what to fix>
  2. [Section] <specific issue and what to fix>

  Fix all of the above, then re-submit for a single confirm pass.
  ```
  ```

  In the `## Notes` section, replace the last bullet:

  Before:
  ```
  - Max 3 review iterations before surfacing to human
  ```

  After:
  ```
  - Max 2 total iterations: initial scan (all issues at once) + confirm pass. If 0 issues → APPROVED immediately, no confirm pass needed.
  ```

  Apply the **identical two edits** to `skills/plan-reviewer/SKILL.md` and `skills/impl-reviewer/SKILL.md`, adjusting the bracket prefix in the issues list to match each skill's existing format:
  - `plan-reviewer` uses `[Task N / Section]`
  - `impl-reviewer` uses `[File:line]`

  The preamble line `Return ALL issues found in this single response — do not stop at the first issue.` is identical in all three files.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Read each of the three SKILL.md files in full. Confirm:
  - Phase 1 context-loading steps are unchanged
  - Phase 2 checklist items are unchanged
  - Phase 3 context-check items are unchanged
  - Only the Output Format block and Notes section were touched
  Run: `make test-unit` — still PASS

---

## Task 2: Update iteration logic in zie-plan + zie-implement

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `commands/zie-plan.md` plan-reviewer gate describes a 2-pass pattern: initial scan → fix all → one confirm pass
- `commands/zie-plan.md` no longer contains `"Max 3 iterations"` in the reviewer gate section
- `commands/zie-plan.md` contains `"Max 2 total iterations"` in the reviewer gate section
- `commands/zie-implement.md` impl-reviewer loop describes the same 2-pass pattern
- `commands/zie-implement.md` no longer contains `"Max 3 total iterations"` (old background-spawn note)
- `commands/zie-implement.md` contains `"Max 2 total iterations"` in the impl-reviewer step
- Edge case: `"0 issues"` or `"APPROVED immediately"` present in both command files

**Files:**
- Modify: `commands/zie-plan.md`
- Modify: `commands/zie-implement.md`
- Modify: `tests/unit/test_reviewer_fail_fast.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_reviewer_fail_fast.py — add new class after TestReviewerOutputInstructions

  class TestCommandIterationLogic:
      def test_zie_plan_no_old_max(self):
          assert "Max 3 iterations" not in command_text("zie-plan"), \
              "zie-plan must not contain old Max 3 iterations"

      def test_zie_plan_new_max(self):
          assert "Max 2 total iterations" in command_text("zie-plan"), \
              "zie-plan must declare Max 2 total iterations"

      def test_zie_plan_confirm_pass(self):
          assert "confirm" in command_text("zie-plan").lower(), \
              "zie-plan reviewer gate must mention a confirm pass"

      def test_zie_plan_zero_issues_fast_path(self):
          text = command_text("zie-plan")
          assert "0 issues" in text or "APPROVED immediately" in text, \
              "zie-plan must describe 0-issues fast path"

      def test_zie_implement_no_old_max(self):
          # old text was "Max 3 total iterations — background spawn counts as iteration 1"
          assert "Max 3 total iterations" not in command_text("zie-implement"), \
              "zie-implement must not contain old Max 3 total iterations"

      def test_zie_implement_new_max(self):
          assert "Max 2 total iterations" in command_text("zie-implement"), \
              "zie-implement must declare Max 2 total iterations"

      def test_zie_implement_confirm_pass(self):
          assert "confirm" in command_text("zie-implement").lower(), \
              "zie-implement impl-reviewer step must mention a confirm pass"

      def test_zie_implement_zero_issues_fast_path(self):
          text = command_text("zie-implement")
          assert "0 issues" in text or "APPROVED immediately" in text, \
              "zie-implement must describe 0-issues fast path"
  ```
  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  **`commands/zie-plan.md`** — update the `## plan-reviewer gate` section (around Lines 65-67):

  Before (Lines 65-67):
  ```
  2. If ❌ Issues Found → fix the plan → re-invoke reviewer → repeat.
     Max 3 iterations → surface to Zie: "Reviewer found persistent issues.
     Review plan manually."
  3. If ✅ Approved → proceed to Zie approval below.
  ```

  After:
  ```
  2. If ❌ Issues Found → fix ALL issues listed → invoke reviewer once more
     as a confirm pass (pass 2 of 2).
     - If confirm pass returns ✅ APPROVED → proceed to Zie approval below.
     - If confirm pass returns ❌ Issues Found again → surface to Zie:
       "Reviewer found persistent issues after fix pass. Review plan manually."
     Max 2 total iterations: initial scan (pass 1) + confirm pass (pass 2).
     If 0 issues on initial scan → APPROVED immediately, no confirm pass needed.
  3. If ✅ Approved on initial scan → proceed to Zie approval below.
  ```

  **`commands/zie-implement.md`** — update Step 6 of the task loop. The relevant passage currently reads:

  Before:
  ```
     - `reviewer_status: issues_found` — halt current task; surface reviewer
       feedback to human; apply fixes; re-run `make test-unit`; re-invoke
       `@agent-impl-reviewer` synchronously (blocking).
       Max 3 total iterations — background spawn counts as iteration 1.
       On APPROVED: clear entry from list; resume current task.
  ```

  After:
  ```
     - `reviewer_status: issues_found` — halt current task; surface reviewer
       feedback to human; apply ALL fixes listed; re-run `make test-unit`;
       re-invoke `@agent-impl-reviewer` synchronously as a confirm pass (blocking).
       Max 2 total iterations: background spawn = pass 1 (initial scan),
       synchronous re-invoke = pass 2 (confirm pass).
       If confirm pass returns ❌ Issues Found → surface to Zie: "Reviewer
       found persistent issues after fix pass. Review manually."
       If 0 issues on initial (background) pass → APPROVED immediately,
       no confirm pass needed.
       On APPROVED at any pass: clear entry from list; resume current task.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Read `commands/zie-plan.md` and `commands/zie-implement.md` in full. Confirm:
  - All other sections (pre-flight checks, brain recall, Zie approval flow, commit step) are unchanged
  - The `Final-wait for still-pending reviewers` block in `zie-implement.md` is unchanged (it already surfaces to Zie after timeout; that path is orthogonal)
  Run: `make test-unit` — still PASS

---

---

## Task 3: Update ADR-014 to reflect new 2-pass iteration model

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- `zie-framework/decisions/ADR-014-async-impl-reviewer-deferred-check.md` contains an `## Amendment` section
- The amendment section contains `"2"` (the new iteration cap)
- The amendment section references `"reviewer-fail-fast"` (the feature that introduced the change)

**Files:**
- Modify: `zie-framework/decisions/ADR-014-async-impl-reviewer-deferred-check.md`
- Modify: `tests/unit/test_reviewer_fail_fast.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_reviewer_fail_fast.py — add new class after TestCommandIterationLogic

  ADR_014 = Path(__file__).parents[2] / "zie-framework" / "decisions" / "ADR-014-async-impl-reviewer-deferred-check.md"

  class TestADR014Amendment:
      def test_adr_014_has_amendment_section(self):
          text = ADR_014.read_text()
          assert "## Amendment" in text, \
              "ADR-014 must contain an ## Amendment section"

      def test_adr_014_amendment_mentions_new_cap(self):
          text = ADR_014.read_text()
          amendment_start = text.index("## Amendment")
          amendment_text = text[amendment_start:]
          assert "2" in amendment_text, \
              "ADR-014 amendment must reference the new iteration cap of 2"

      def test_adr_014_amendment_mentions_reviewer_fail_fast(self):
          text = ADR_014.read_text()
          amendment_start = text.index("## Amendment")
          amendment_text = text[amendment_start:]
          assert "reviewer-fail-fast" in amendment_text, \
              "ADR-014 amendment must reference the reviewer-fail-fast feature"
  ```
  Run: `make test-unit` — must FAIL (`## Amendment` not yet present)

- [ ] **Step 2: Implement (GREEN)**

  **`zie-framework/decisions/ADR-014-async-impl-reviewer-deferred-check.md`** — append at the bottom of the file:

  ```markdown
  ## Amendment

  Amended by `reviewer-fail-fast` (2026-03-24): iteration cap reduced from 3 to 2
  (initial scan + confirm pass) for `impl-reviewer` in `zie-implement.md`.

  The background spawn remains pass 1 (initial scan). If `issues_found`, a single
  synchronous confirm pass (pass 2) is invoked after fixes are applied. There is no
  third iteration — persistent issues after the confirm pass are surfaced directly to
  Zie. This replaces the previous "Max 3 total iterations" note in the Decision section.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Read `zie-framework/decisions/ADR-014-async-impl-reviewer-deferred-check.md` in full. Confirm:
  - Context, Decision, and Consequences sections are untouched
  - Only the new `## Amendment` section was appended
  Run: `make test-unit` — still PASS

---

*Commit: `git add skills/spec-reviewer/SKILL.md skills/plan-reviewer/SKILL.md skills/impl-reviewer/SKILL.md commands/zie-plan.md commands/zie-implement.md zie-framework/decisions/ADR-014-async-impl-reviewer-deferred-check.md tests/unit/test_reviewer_fail_fast.py && git commit -m "feat: reviewer-fail-fast"`*
