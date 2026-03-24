---
approved: false
approved_at: ~
backlog: backlog/spec-design-fast-path.md
spec: specs/2026-03-24-spec-design-fast-path-design.md
---

# spec-design Fast Path for Complete Backlog Items — Implementation Plan

**Goal:** Add a completeness check at Phase 1 of the `spec-design` skill. When the backlog item's Problem, Motivation, and Rough Scope sections are each substantive (≥2 sentences of non-trivial content), skip the clarifying question phase and go directly to proposing 2–3 approaches. Thin or missing sections fall through to the existing question flow unchanged.

**Architecture:** Single file edit — `skills/spec-design/SKILL.md`. Insert a completeness-check block before Step 1 (clarifying questions). The check evaluates the three sections inline and branches: fast-path lands at Step 2 (approach proposal); normal path continues to Step 1 as today.

**Tech Stack:** Markdown (skill definition), pytest (string-content validation)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/spec-design/SKILL.md` | Add completeness check block before Step 1 |
| Create | `tests/unit/test_spec_design_fast_path.py` | Validate fast-path text present in SKILL.md |

---

## Task 1: Add completeness check to `skills/spec-design/SKILL.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `skills/spec-design/SKILL.md` contains a completeness check block that reads Problem, Motivation, and Rough Scope from the backlog item
- The block defines "substantive" as each section having ≥2 sentences of non-trivial content (not just "TBD" or a single word)
- A fast-path branch is present: when all three sections are substantive → skip to Step 2 (approach proposal)
- A fallback branch is present: when any section is thin or missing → continue to Step 1 (clarifying questions)
- The fast-path does not apply when no backlog item is provided (inline idea path)
- All existing steps (1 through 9) are unchanged in content and order

**Files:**
- Modify: `skills/spec-design/SKILL.md`
- Create: `tests/unit/test_spec_design_fast_path.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_spec_design_fast_path.py
  from pathlib import Path

  SKILL_PATH = Path(__file__).parents[2] / "skills" / "spec-design" / "SKILL.md"


  def skill_text() -> str:
      return SKILL_PATH.read_text()


  class TestSpecDesignFastPath:
      def test_completeness_check_logic_present(self):
          text = skill_text()
          assert "completeness" in text.lower(), \
              "SKILL.md must contain a completeness check"

      def test_substantive_definition_present(self):
          text = skill_text()
          assert "2 sentences" in text or "≥2 sentences" in text or "two sentences" in text.lower(), \
              "SKILL.md must define 'substantive' as ≥2 sentences"

      def test_fast_path_branch_present(self):
          text = skill_text()
          assert "fast" in text.lower() or "fast-path" in text.lower() or "fast path" in text.lower(), \
              "SKILL.md must contain a fast-path branch"

      def test_fast_path_skips_to_approach_proposal(self):
          text = skill_text()
          # Fast path must reference skipping to Step 2 / approach proposal
          assert "approach" in text.lower(), \
              "SKILL.md fast path must reference approach proposal"

      def test_fallback_to_questions_present(self):
          text = skill_text()
          # Normal path fallback must reference clarifying questions
          assert "clarif" in text.lower(), \
              "SKILL.md must retain reference to clarifying questions fallback"

      def test_fast_path_not_applied_without_backlog(self):
          text = skill_text()
          assert "backlog" in text.lower(), \
              "SKILL.md completeness check must be scoped to backlog items"

      def test_argument_precedence_documented(self):
          text = skill_text()
          # The completeness check block must document how $ARGUMENTS[1] interacts
          assert "quick" in text and "full" in text, \
              "SKILL.md must reference both 'quick' and 'full' modes in the completeness check block"

      def test_existing_steps_intact(self):
          text = skill_text()
          # All nine original steps must remain
          for step_phrase in (
              "Understand the idea",
              "Propose 2-3 approaches",
              "Present design sections",
              "Write spec",
              "Spec reviewer loop",
              "Record approval",
              "Store spec approval",
              "Ask user to review",
              "Print handoff",
          ):
              assert step_phrase in text, \
                  f"SKILL.md must retain existing step: '{step_phrase}'"
  ```

  Run: `make test-unit` — must FAIL (completeness check text not yet in SKILL.md)

- [ ] **Step 2: Implement (GREEN)**

  In `skills/spec-design/SKILL.md`, insert the following block immediately before the `## Steps` section header line (between the `## เตรียม context` section and `## Steps`):

  ```markdown
  ## Completeness Check (fast path)

  When `$ARGUMENTS[0]` is a backlog slug, read the backlog item at
  `zie-framework/backlog/<slug>.md` before starting the question flow.
  Evaluate the three sections:

  - **Problem** — is there substantive content? (≥2 sentences, not just "TBD"
    or a single word)
  - **Motivation** — is there substantive content? (≥2 sentences, not just
    "TBD" or a single word)
  - **Rough Scope** — is there substantive content? (≥2 sentences, not just
    "TBD" or a single word)

  **Fast path:** If all three sections are substantive → skip Step 1
  (clarifying questions) entirely and go directly to Step 2 (propose 2-3
  approaches), using the backlog content to inform the proposals.

  **Normal path:** If any section is thin, missing, or absent → fall through
  to Step 1 (clarifying questions) as normal.

  This fast-path applies only when a backlog item is provided. When no backlog
  slug is given (inline idea path), always start at Step 1.

  **`$ARGUMENTS[1]` mode precedence:** When `$ARGUMENTS[1]` is `quick`, that
  mode takes effect and this check is skipped. When `full`, clarifying questions
  are always asked regardless of completeness.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read the full `skills/spec-design/SKILL.md` to confirm:
  - The new block sits between `## เตรียม context` and `## Steps` with no stray blank lines breaking adjacent sections
  - Steps 1–9 are word-for-word identical to the pre-change version
  - No duplicate headings introduced

  Run: `make test-unit` — still PASS

---

*Commit: `git add skills/spec-design/SKILL.md tests/unit/test_spec_design_fast_path.py && git commit -m "feat: spec-design fast path for complete backlog items"`*
