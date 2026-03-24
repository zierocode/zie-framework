---
approved: true
approved_at: 2026-03-24
backlog: backlog/skills-fork-context.md
spec: specs/2026-03-24-skills-fork-context-design.md
---

# Skills context:fork for Isolated Reviewer Execution — Implementation Plan

**Goal:** Add `context: fork` and `agent:` frontmatter to the three reviewer skills so Claude Code executes each review in an isolated subagent context, keeping all Phase 1–3 file reads and analysis out of the main conversation window.
**Architecture:** Pure frontmatter additions to existing SKILL.md files. No phase logic changes. New pytest test class in a new file asserts all three skills carry the correct frontmatter fields after the change.
**Tech Stack:** Markdown (SKILL.md frontmatter), Python 3.x, pytest

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/spec-reviewer/SKILL.md` | Add `context: fork`, `agent: Explore`, `allowed-tools: Read, Grep, Glob` |
| Modify | `skills/plan-reviewer/SKILL.md` | Add `context: fork`, `agent: Explore`, `allowed-tools: Read, Grep, Glob` |
| Modify | `skills/impl-reviewer/SKILL.md` | Add `context: fork`, `agent: general-purpose`, `allowed-tools: Read, Grep, Glob, Bash` |
| Create | `tests/unit/test_skills_fork_context.py` | Pytest assertions verifying frontmatter fields are present and correct per skill |

---

## Task 1: Add `context: fork` and `agent: Explore` to spec-reviewer and plan-reviewer

<!-- depends_on: none -->

**Acceptance Criteria:**
- `skills/spec-reviewer/SKILL.md` frontmatter contains `context: fork`, `agent: Explore`, `allowed-tools: Read, Grep, Glob`
- `skills/plan-reviewer/SKILL.md` frontmatter contains `context: fork`, `agent: Explore`, `allowed-tools: Read, Grep, Glob`
- All existing `test_reviewer_depth.py` tests continue to pass (no phase logic changed)
- `make test-unit` exits 0

**Files:**
- Modify: `skills/spec-reviewer/SKILL.md`
- Modify: `skills/plan-reviewer/SKILL.md`
- Create: `tests/unit/test_skills_fork_context.py`

- [ ] **Step 1: Write failing tests (RED)**

  Create `tests/unit/test_skills_fork_context.py` with assertions for spec-reviewer and plan-reviewer frontmatter fields. The test file must parse only the YAML frontmatter block (lines between the first and second `---` delimiters).

  ```python
  # tests/unit/test_skills_fork_context.py

  import re
  from pathlib import Path

  ROOT = Path(__file__).parent.parent.parent
  SKILLS = ROOT / "skills"


  def read_frontmatter(skill_name: str) -> str:
      """Return the raw text between the first pair of --- delimiters."""
      text = (SKILLS / skill_name / "SKILL.md").read_text()
      match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
      assert match, f"{skill_name}/SKILL.md has no frontmatter block"
      return match.group(1)


  class TestSpecReviewerForkContext:
      def test_has_context_fork(self):
          fm = read_frontmatter("spec-reviewer")
          assert "context: fork" in fm, \
              "spec-reviewer frontmatter must contain 'context: fork'"

      def test_has_agent_explore(self):
          fm = read_frontmatter("spec-reviewer")
          assert "agent: Explore" in fm, \
              "spec-reviewer frontmatter must contain 'agent: Explore'"

      def test_has_allowed_tools(self):
          fm = read_frontmatter("spec-reviewer")
          assert "allowed-tools:" in fm, \
              "spec-reviewer frontmatter must contain 'allowed-tools:'"

      def test_allowed_tools_read(self):
          fm = read_frontmatter("spec-reviewer")
          assert "Read" in fm, \
              "spec-reviewer allowed-tools must include Read"

      def test_allowed_tools_grep(self):
          fm = read_frontmatter("spec-reviewer")
          assert "Grep" in fm, \
              "spec-reviewer allowed-tools must include Grep"

      def test_allowed_tools_glob(self):
          fm = read_frontmatter("spec-reviewer")
          assert "Glob" in fm, \
              "spec-reviewer allowed-tools must include Glob"

      def test_no_bash_in_allowed_tools(self):
          fm = read_frontmatter("spec-reviewer")
          assert "Bash" not in fm, \
              "spec-reviewer is Explore agent — Bash must not appear in frontmatter"


  class TestPlanReviewerForkContext:
      def test_has_context_fork(self):
          fm = read_frontmatter("plan-reviewer")
          assert "context: fork" in fm, \
              "plan-reviewer frontmatter must contain 'context: fork'"

      def test_has_agent_explore(self):
          fm = read_frontmatter("plan-reviewer")
          assert "agent: Explore" in fm, \
              "plan-reviewer frontmatter must contain 'agent: Explore'"

      def test_has_allowed_tools(self):
          fm = read_frontmatter("plan-reviewer")
          assert "allowed-tools:" in fm, \
              "plan-reviewer frontmatter must contain 'allowed-tools:'"

      def test_allowed_tools_read(self):
          fm = read_frontmatter("plan-reviewer")
          assert "Read" in fm, \
              "plan-reviewer allowed-tools must include Read"

      def test_allowed_tools_grep(self):
          fm = read_frontmatter("plan-reviewer")
          assert "Grep" in fm, \
              "plan-reviewer allowed-tools must include Grep"

      def test_allowed_tools_glob(self):
          fm = read_frontmatter("plan-reviewer")
          assert "Glob" in fm, \
              "plan-reviewer allowed-tools must include Glob"

      def test_no_bash_in_allowed_tools(self):
          fm = read_frontmatter("plan-reviewer")
          assert "Bash" not in fm, \
              "plan-reviewer is Explore agent — Bash must not appear in frontmatter"
  ```

  Run: `make test-unit` — must FAIL (`context: fork` not yet in either SKILL.md)

- [ ] **Step 2: Implement (GREEN)**

  Replace the frontmatter block in `skills/spec-reviewer/SKILL.md`:

  ```yaml
  ---
  name: spec-reviewer
  description: Review a design spec for completeness, clarity, and YAGNI. Returns APPROVED or Issues Found with specific feedback.
  context: fork
  agent: Explore
  allowed-tools: Read, Grep, Glob
  ---
  ```

  Replace the frontmatter block in `skills/plan-reviewer/SKILL.md`:

  ```yaml
  ---
  name: plan-reviewer
  description: Review an implementation plan for completeness, TDD structure, and task granularity. Returns APPROVED or Issues Found with specific feedback.
  context: fork
  agent: Explore
  allowed-tools: Read, Grep, Glob
  ---
  ```

  No changes to any phase content below the second `---` in either file.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Confirm `context: fork` appears exactly once in each of the two files (no duplicate frontmatter blocks).
  Confirm all `test_reviewer_depth.py` tests still pass — phase logic is untouched.

  Run: `make test-unit` — still PASS

---

## Task 2: Add `context: fork` and `agent: general-purpose` to impl-reviewer

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `skills/impl-reviewer/SKILL.md` frontmatter contains `context: fork`, `agent: general-purpose`, `allowed-tools: Read, Grep, Glob, Bash`
- `Bash` is present in `allowed-tools` for impl-reviewer and absent for spec-reviewer and plan-reviewer (spec already asserted in Task 1)
- All existing `test_reviewer_depth.py` tests continue to pass
- `make test-unit` exits 0

**Files:**
- Modify: `skills/impl-reviewer/SKILL.md`
- Modify: `tests/unit/test_skills_fork_context.py`

- [ ] **Step 1: Write failing tests (RED)**

  Append a new class to `tests/unit/test_skills_fork_context.py`:

  ```python
  # tests/unit/test_skills_fork_context.py — append after TestPlanReviewerForkContext

  class TestImplReviewerForkContext:
      def test_has_context_fork(self):
          fm = read_frontmatter("impl-reviewer")
          assert "context: fork" in fm, \
              "impl-reviewer frontmatter must contain 'context: fork'"

      def test_has_agent_general_purpose(self):
          fm = read_frontmatter("impl-reviewer")
          assert "agent: general-purpose" in fm, \
              "impl-reviewer frontmatter must contain 'agent: general-purpose'"

      def test_not_agent_explore(self):
          fm = read_frontmatter("impl-reviewer")
          assert "agent: Explore" not in fm, \
              "impl-reviewer must use general-purpose agent, not Explore"

      def test_has_allowed_tools(self):
          fm = read_frontmatter("impl-reviewer")
          assert "allowed-tools:" in fm, \
              "impl-reviewer frontmatter must contain 'allowed-tools:'"

      def test_allowed_tools_read(self):
          fm = read_frontmatter("impl-reviewer")
          assert "Read" in fm, \
              "impl-reviewer allowed-tools must include Read"

      def test_allowed_tools_grep(self):
          fm = read_frontmatter("impl-reviewer")
          assert "Grep" in fm, \
              "impl-reviewer allowed-tools must include Grep"

      def test_allowed_tools_glob(self):
          fm = read_frontmatter("impl-reviewer")
          assert "Glob" in fm, \
              "impl-reviewer allowed-tools must include Glob"

      def test_allowed_tools_bash(self):
          fm = read_frontmatter("impl-reviewer")
          assert "Bash" in fm, \
              "impl-reviewer allowed-tools must include Bash (general-purpose agent needs shell access)"
  ```

  Run: `make test-unit` — must FAIL (`context: fork` not yet in impl-reviewer SKILL.md)

- [ ] **Step 2: Implement (GREEN)**

  Replace the frontmatter block in `skills/impl-reviewer/SKILL.md`:

  ```yaml
  ---
  name: impl-reviewer
  description: Review a completed task implementation against its acceptance criteria. Returns APPROVED or Issues Found with specific feedback.
  context: fork
  agent: general-purpose
  allowed-tools: Read, Grep, Glob, Bash
  ---
  ```

  No changes to any phase content below the second `---`.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Confirm `agent: general-purpose` appears in impl-reviewer and `agent: Explore` does not.
  Confirm `Bash` appears in impl-reviewer frontmatter and is absent from spec-reviewer and plan-reviewer frontmatter (cross-skill boundary guard).

  Run: `make test-unit` — still PASS

---

## Task 3: Frontmatter parse robustness tests

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- `read_frontmatter()` helper raises `AssertionError` with a clear message when given a skill with no frontmatter block
- All three reviewer skills' frontmatter fields are validated as exact strings (not substring-of-value false positives)
- `make test-unit` exits 0

**Files:**
- Modify: `tests/unit/test_skills_fork_context.py`

- [ ] **Step 1: Write failing tests (RED)**

  Append a new class to `tests/unit/test_skills_fork_context.py`:

  ```python
  # tests/unit/test_skills_fork_context.py — append after TestImplReviewerForkContext

  import pytest
  import tempfile
  import os


  class TestReadFrontmatterHelper:
      def test_raises_on_missing_frontmatter(self, tmp_path, monkeypatch):
          """read_frontmatter must assert-fail on a SKILL.md with no --- block."""
          fake_skill = tmp_path / "no-fm" / "SKILL.md"
          fake_skill.parent.mkdir()
          fake_skill.write_text("# No frontmatter here\n\nJust content.\n")
          monkeypatch.setattr(
              "tests.unit.test_skills_fork_context.SKILLS", tmp_path
          )
          with pytest.raises(AssertionError, match="no-fm/SKILL.md has no frontmatter block"):
              read_frontmatter("no-fm")

      def test_spec_reviewer_context_fork_is_exact_field(self):
          """'context: fork' must be a standalone field, not a substring like 'context: fork-extra'."""
          fm = read_frontmatter("spec-reviewer")
          lines = fm.splitlines()
          assert any(line.strip() == "context: fork" for line in lines), \
              "spec-reviewer: 'context: fork' must appear as an exact line in frontmatter"

      def test_plan_reviewer_context_fork_is_exact_field(self):
          fm = read_frontmatter("plan-reviewer")
          lines = fm.splitlines()
          assert any(line.strip() == "context: fork" for line in lines), \
              "plan-reviewer: 'context: fork' must appear as an exact line in frontmatter"

      def test_impl_reviewer_context_fork_is_exact_field(self):
          fm = read_frontmatter("impl-reviewer")
          lines = fm.splitlines()
          assert any(line.strip() == "context: fork" for line in lines), \
              "impl-reviewer: 'context: fork' must appear as an exact line in frontmatter"

      def test_spec_reviewer_agent_is_exact_field(self):
          fm = read_frontmatter("spec-reviewer")
          lines = fm.splitlines()
          assert any(line.strip() == "agent: Explore" for line in lines), \
              "spec-reviewer: 'agent: Explore' must appear as an exact line in frontmatter"

      def test_plan_reviewer_agent_is_exact_field(self):
          fm = read_frontmatter("plan-reviewer")
          lines = fm.splitlines()
          assert any(line.strip() == "agent: Explore" for line in lines), \
              "plan-reviewer: 'agent: Explore' must appear as an exact line in frontmatter"

      def test_impl_reviewer_agent_is_exact_field(self):
          fm = read_frontmatter("impl-reviewer")
          lines = fm.splitlines()
          assert any(line.strip() == "agent: general-purpose" for line in lines), \
              "impl-reviewer: 'agent: general-purpose' must appear as an exact line in frontmatter"
  ```

  Run: `make test-unit` — the monkeypatch test will FAIL (monkeypatch target path needs adjustment to match module-level `SKILLS` variable — this is the intentional RED signal confirming the test reaches the helper correctly)

  Note: the exact-field line tests will pass if Tasks 1–2 are done correctly; the RED signal is the `test_raises_on_missing_frontmatter` monkeypatch test until the import path is confirmed correct.

- [ ] **Step 2: Implement (GREEN)**

  Fix the monkeypatch target in `test_raises_on_missing_frontmatter` to use the correct fully-qualified module attribute path. The correct string is:

  ```python
  # Correct monkeypatch target — patch SKILLS in this module's own namespace
  monkeypatch.setattr(
      "tests.unit.test_skills_fork_context.SKILLS", tmp_path
  )
  ```

  This patches the `SKILLS` variable at its definition site in `tests.unit.test_skills_fork_context`, which is the name `read_frontmatter` closes over at call time.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Remove any `import tempfile` and `import os` lines added in Step 1 if they are unused after the final implementation (keep only `pytest` and `re` plus `pathlib.Path`).
  Confirm no duplicate imports at the top of `test_skills_fork_context.py`.

  Run: `make test-unit` — still PASS

---

*Commit: `git add skills/spec-reviewer/SKILL.md skills/plan-reviewer/SKILL.md skills/impl-reviewer/SKILL.md tests/unit/test_skills_fork_context.py && git commit -m "feat: context:fork isolation for reviewer skills (spec, plan, impl)"`*
