---
approved: true
approved_at: 2026-03-24
backlog: backlog/skills-frontmatter-hardening.md
spec: specs/2026-03-24-skills-frontmatter-hardening-design.md
---

# Skills Frontmatter Hardening — Implementation Plan

**Goal:** Add targeted frontmatter fields (`user-invocable`, `allowed-tools`, `effort`) to all 10 SKILL.md files to prevent unwanted auto-invocation, hide internal skills from the command picker, restrict reviewer tools to read-only, and route high-effort skills to full thinking budget.
**Architecture:** Frontmatter-only changes — no skill content, logic, or command files are touched. Skills are grouped into three cohorts by the fields they receive: (1) internal subagent skills get `user-invocable: false`, (2) reviewer skills additionally get `allowed-tools: Read, Grep, Glob`, (3) planning skills get `effort: high`. `verify` and `debug` require only `user-invocable: false` based on their roles as internal orchestration helpers; `spec-design`, `write-plan`, and `verify` retain user-invocability per spec.
**Tech Stack:** Markdown (SKILL.md frontmatter), pytest (YAML frontmatter parse + field assertion)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/spec-reviewer/SKILL.md` | Add `user-invocable: false`, `allowed-tools` |
| Modify | `skills/plan-reviewer/SKILL.md` | Add `user-invocable: false`, `allowed-tools` |
| Modify | `skills/impl-reviewer/SKILL.md` | Add `user-invocable: false`, `allowed-tools` |
| Modify | `skills/tdd-loop/SKILL.md` | Add `user-invocable: false` |
| Modify | `skills/retro-format/SKILL.md` | Add `user-invocable: false` |
| Modify | `skills/test-pyramid/SKILL.md` | Add `user-invocable: false` |
| Modify | `skills/debug/SKILL.md` | Add `user-invocable: false` |
| Modify | `skills/spec-design/SKILL.md` | Add `effort: high` |
| Modify | `skills/write-plan/SKILL.md` | Add `effort: high` |
| Create | `tests/unit/test_skills_frontmatter.py` | Validate frontmatter fields exist and parse correctly |

---

## Task 1: Add `user-invocable: false` and `allowed-tools` to reviewer skills

<!-- depends_on: none -->

**Acceptance Criteria:**
- `skills/spec-reviewer/SKILL.md` frontmatter contains `user-invocable: false` and `allowed-tools: Read, Grep, Glob`
- `skills/plan-reviewer/SKILL.md` frontmatter contains `user-invocable: false` and `allowed-tools: Read, Grep, Glob`
- `skills/impl-reviewer/SKILL.md` frontmatter contains `user-invocable: false` and `allowed-tools: Read, Grep, Glob`
- Tests parse frontmatter via PyYAML and assert all three fields per skill
- `make test-unit` passes after implementation

**Files:**
- Create: `tests/unit/test_skills_frontmatter.py`
- Modify: `skills/spec-reviewer/SKILL.md`
- Modify: `skills/plan-reviewer/SKILL.md`
- Modify: `skills/impl-reviewer/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_skills_frontmatter.py

  import os
  import yaml

  REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


  def read_frontmatter(skill_name: str) -> dict:
      """Parse YAML frontmatter block from a SKILL.md file."""
      path = os.path.join(REPO_ROOT, "skills", skill_name, "SKILL.md")
      with open(path) as f:
          content = f.read()
      # frontmatter is between the first and second ---
      if not content.startswith("---"):
          return {}
      parts = content.split("---", 2)
      if len(parts) < 3:
          return {}
      return yaml.safe_load(parts[1]) or {}


  REVIEWER_SKILLS = ["spec-reviewer", "plan-reviewer", "impl-reviewer"]


  class TestReviewerSkillsFrontmatter:
      def test_spec_reviewer_user_invocable_false(self):
          fm = read_frontmatter("spec-reviewer")
          assert fm.get("user-invocable") is False, \
              "spec-reviewer must have user-invocable: false"

      def test_spec_reviewer_allowed_tools(self):
          fm = read_frontmatter("spec-reviewer")
          assert fm.get("allowed-tools") == "Read, Grep, Glob", \
              "spec-reviewer must have allowed-tools: Read, Grep, Glob"

      def test_plan_reviewer_user_invocable_false(self):
          fm = read_frontmatter("plan-reviewer")
          assert fm.get("user-invocable") is False, \
              "plan-reviewer must have user-invocable: false"

      def test_plan_reviewer_allowed_tools(self):
          fm = read_frontmatter("plan-reviewer")
          assert fm.get("allowed-tools") == "Read, Grep, Glob", \
              "plan-reviewer must have allowed-tools: Read, Grep, Glob"

      def test_impl_reviewer_user_invocable_false(self):
          fm = read_frontmatter("impl-reviewer")
          assert fm.get("user-invocable") is False, \
              "impl-reviewer must have user-invocable: false"

      def test_impl_reviewer_allowed_tools(self):
          fm = read_frontmatter("impl-reviewer")
          assert fm.get("allowed-tools") == "Read, Grep, Glob", \
              "impl-reviewer must have allowed-tools: Read, Grep, Glob"
  ```
  Run: `make test-unit` — must FAIL (fields not yet present)

- [ ] **Step 2: Implement (GREEN)**

  Add these lines to the existing frontmatter block of each reviewer skill (insert after the `description:` line, before the closing `---`):

  **`skills/spec-reviewer/SKILL.md`** — frontmatter becomes:
  ```yaml
  ---
  name: spec-reviewer
  description: Review a design spec for completeness, clarity, and YAGNI. Returns APPROVED or Issues Found with specific feedback.
  user-invocable: false
  allowed-tools: Read, Grep, Glob
  ---
  ```

  **`skills/plan-reviewer/SKILL.md`** — frontmatter becomes:
  ```yaml
  ---
  name: plan-reviewer
  description: Review an implementation plan for completeness, TDD structure, and task granularity. Returns APPROVED or Issues Found with specific feedback.
  user-invocable: false
  allowed-tools: Read, Grep, Glob
  ---
  ```

  **`skills/impl-reviewer/SKILL.md`** — frontmatter becomes:
  ```yaml
  ---
  name: impl-reviewer
  description: Review a completed task implementation against its acceptance criteria. Returns APPROVED or Issues Found with specific feedback.
  user-invocable: false
  allowed-tools: Read, Grep, Glob
  ---
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Confirm all three frontmatter blocks use the canonical PascalCase tool names (`Read, Grep, Glob`) with no typos. No structural changes required.
  Run: `make test-unit` — still PASS

---

## Task 2: Add `user-invocable: false` to internal process skills

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `skills/tdd-loop/SKILL.md` frontmatter contains `user-invocable: false`
- `skills/retro-format/SKILL.md` frontmatter contains `user-invocable: false`
- `skills/test-pyramid/SKILL.md` frontmatter contains `user-invocable: false`
- `skills/debug/SKILL.md` frontmatter contains `user-invocable: false`
- Tests assert the field for all four skills
- `make test-unit` passes after implementation

**Files:**
- Modify: `tests/unit/test_skills_frontmatter.py`
- Modify: `skills/tdd-loop/SKILL.md`
- Modify: `skills/retro-format/SKILL.md`
- Modify: `skills/test-pyramid/SKILL.md`
- Modify: `skills/debug/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_skills_frontmatter.py — append after TestReviewerSkillsFrontmatter

  class TestInternalProcessSkillsFrontmatter:
      def test_tdd_loop_user_invocable_false(self):
          fm = read_frontmatter("tdd-loop")
          assert fm.get("user-invocable") is False, \
              "tdd-loop must have user-invocable: false"

      def test_retro_format_user_invocable_false(self):
          fm = read_frontmatter("retro-format")
          assert fm.get("user-invocable") is False, \
              "retro-format must have user-invocable: false"

      def test_test_pyramid_user_invocable_false(self):
          fm = read_frontmatter("test-pyramid")
          assert fm.get("user-invocable") is False, \
              "test-pyramid must have user-invocable: false"

      def test_debug_user_invocable_false(self):
          fm = read_frontmatter("debug")
          assert fm.get("user-invocable") is False, \
              "debug must have user-invocable: false"
  ```
  Run: `make test-unit` — must FAIL (fields not yet present)

- [ ] **Step 2: Implement (GREEN)**

  Add `user-invocable: false` to each skill's existing frontmatter block (insert after the last existing field, before the closing `---`):

  **`skills/tdd-loop/SKILL.md`** — frontmatter becomes:
  ```yaml
  ---
  name: tdd-loop
  description: TDD RED-GREEN-REFACTOR loop guide for zie-framework builds
  type: process
  user-invocable: false
  ---
  ```

  **`skills/retro-format/SKILL.md`** — frontmatter becomes:
  ```yaml
  ---
  name: retro-format
  description: Retrospective format and ADR structure for /zie-retro
  type: reference
  user-invocable: false
  ---
  ```

  **`skills/test-pyramid/SKILL.md`** — frontmatter becomes:
  ```yaml
  ---
  name: test-pyramid
  description: Testing strategy by project type — which tests to write, when to run them
  type: reference
  user-invocable: false
  ---
  ```

  **`skills/debug/SKILL.md`** — frontmatter becomes:
  ```yaml
  ---
  name: debug
  description: Systematic debugging — reproduce, isolate, fix, verify. Uses zie-memory to surface known failure patterns.
  metadata:
    zie_memory_enabled: true
  user-invocable: false
  ---
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Verify `user-invocable: false` is a top-level key (not nested under `metadata:`) in all four files.
  Run: `make test-unit` — still PASS

---

## Task 3: Add `effort: high` to planning skills

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- `skills/spec-design/SKILL.md` frontmatter contains `effort: high`
- `skills/write-plan/SKILL.md` frontmatter contains `effort: high`
- Tests assert the field for both skills
- `make test-unit` passes after implementation

**Files:**
- Modify: `tests/unit/test_skills_frontmatter.py`
- Modify: `skills/spec-design/SKILL.md`
- Modify: `skills/write-plan/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_skills_frontmatter.py — append after TestInternalProcessSkillsFrontmatter

  class TestPlanningSkillsFrontmatter:
      def test_spec_design_effort_high(self):
          fm = read_frontmatter("spec-design")
          assert fm.get("effort") == "high", \
              "spec-design must have effort: high"

      def test_write_plan_effort_high(self):
          fm = read_frontmatter("write-plan")
          assert fm.get("effort") == "high", \
              "write-plan must have effort: high"
  ```
  Run: `make test-unit` — must FAIL (fields not yet present)

- [ ] **Step 2: Implement (GREEN)**

  **`skills/spec-design/SKILL.md`** — frontmatter becomes:
  ```yaml
  ---
  name: spec-design
  description: Brainstorm and write a design spec for a new feature. Saves to zie-framework/specs/.
  metadata:
    zie_memory_enabled: true
  effort: high
  ---
  ```

  **`skills/write-plan/SKILL.md`** — frontmatter becomes:
  ```yaml
  ---
  name: write-plan
  description: Write a detailed implementation plan from an approved spec. Saves to zie-framework/plans/.
  metadata:
    zie_memory_enabled: true
  effort: high
  ---
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Verify `effort: high` is a top-level key (not nested under `metadata:`) in both files. No other changes.
  Run: `make test-unit` — still PASS

---

## Task 4: Verify `verify` skill requires no changes + regression sweep

<!-- depends_on: Task 3 -->

**Acceptance Criteria:**
- `skills/verify/SKILL.md` has no `user-invocable: false` (it is user-facing)
- All 10 SKILL.md files remain parseable as valid YAML frontmatter
- Full `make test-unit` suite passes with no regressions from prior test classes

**Files:**
- Modify: `tests/unit/test_skills_frontmatter.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_skills_frontmatter.py — append after TestPlanningSkillsFrontmatter

  ALL_SKILLS = [
      "spec-reviewer", "plan-reviewer", "impl-reviewer",
      "tdd-loop", "retro-format", "test-pyramid", "debug",
      "spec-design", "write-plan", "verify",
  ]


  class TestAllSkillsFrontmatterValid:
      def test_all_skills_have_parseable_frontmatter(self):
          """Every SKILL.md must have a valid YAML frontmatter block."""
          for skill in ALL_SKILLS:
              fm = read_frontmatter(skill)
              assert isinstance(fm, dict), \
                  f"{skill}/SKILL.md frontmatter must parse to a dict, got {type(fm)}"
              assert "name" in fm, \
                  f"{skill}/SKILL.md frontmatter must contain a 'name' field"

      def test_verify_is_user_invocable(self):
          """verify is a user-facing skill — must NOT have user-invocable: false."""
          fm = read_frontmatter("verify")
          assert fm.get("user-invocable") is not False, \
              "verify must NOT have user-invocable: false — it is user-facing"
  ```
  Run: `make test-unit` — `test_verify_is_user_invocable` passes immediately; `test_all_skills_have_parseable_frontmatter` must PASS only after Tasks 1-3 are complete. If run before Tasks 1-3, it will PASS vacuously (existing frontmatter is already valid YAML). Treat this task's primary value as the regression net.

- [ ] **Step 2: Implement (GREEN)**
  No implementation changes. This task is test-only. Confirm all tests from Tasks 1-3 are still green.
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Review `test_skills_frontmatter.py` for any duplicated assertions across classes. If `read_frontmatter` is duplicating logic from `test_fork_superpowers_skills.py`, note for future consolidation but do not refactor now (out of scope).
  Run: `make test-unit` — still PASS

---

*Commit: `git add skills/spec-reviewer/SKILL.md skills/plan-reviewer/SKILL.md skills/impl-reviewer/SKILL.md skills/tdd-loop/SKILL.md skills/retro-format/SKILL.md skills/test-pyramid/SKILL.md skills/debug/SKILL.md skills/spec-design/SKILL.md skills/write-plan/SKILL.md tests/unit/test_skills_frontmatter.py && git commit -m "feat: skills-frontmatter-hardening — user-invocable, allowed-tools, effort fields"`*
