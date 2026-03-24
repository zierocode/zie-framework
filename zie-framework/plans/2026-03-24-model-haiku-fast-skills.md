---
approved: true
approved_at: 2026-03-24
backlog: backlog/model-haiku-fast-skills.md
spec: specs/2026-03-24-model-haiku-fast-skills-design.md
---
# model:haiku + effort:low for Fast/Status Skills — Implementation Plan

**Goal:** Add `model` and `effort` frontmatter fields to skill and command files to route fast/status tasks to Claude Haiku and pin deep-design tasks to Sonnet with `effort: high`, making cost/latency routing explicit and version-stable.
**Architecture:** Additive-only changes — prepend or extend YAML frontmatter blocks in 10 files. No skill content, logic, tool allowlists, or test logic changes. One new pytest test class validates that each modified file's frontmatter parses cleanly and contains the expected keys.
**Tech Stack:** Python 3.x, PyYAML (stdlib-compatible via `yaml` — already available in test env), pytest

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-status.md` | Add `model: haiku`, `effort: low` to frontmatter |
| Modify | `skills/spec-reviewer/SKILL.md` | Add `model: haiku`, `effort: low` to frontmatter |
| Modify | `skills/plan-reviewer/SKILL.md` | Add `model: haiku`, `effort: low` to frontmatter |
| Modify | `skills/impl-reviewer/SKILL.md` | Add `model: haiku`, `effort: low` to frontmatter |
| Modify | `skills/spec-design/SKILL.md` | Add `model: sonnet`, `effort: high` to frontmatter |
| Modify | `skills/write-plan/SKILL.md` | Add `model: sonnet`, `effort: high` to frontmatter |
| Modify | `commands/zie-spec.md` | Add `effort: high` to frontmatter |
| Modify | `commands/zie-plan.md` | Add `effort: high` to frontmatter |
| Modify | `commands/zie-implement.md` | Add `effort: medium` to frontmatter |
| Modify | `commands/zie-fix.md` | Add `effort: medium` to frontmatter |
| Modify | `tests/unit/test_model_effort_frontmatter.py` | New test class; verify frontmatter keys |

---

## Task 1: Add model:haiku + effort:low to reviewer skills and zie-status

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-status.md` frontmatter contains `model: haiku` and `effort: low`
- `skills/spec-reviewer/SKILL.md` frontmatter contains `model: haiku` and `effort: low`
- `skills/plan-reviewer/SKILL.md` frontmatter contains `model: haiku` and `effort: low`
- `skills/impl-reviewer/SKILL.md` frontmatter contains `model: haiku` and `effort: low`
- All four files parse as valid YAML in the frontmatter block
- No existing content, checklist, or tool allowlist in any file is modified

**Files:**
- Modify: `commands/zie-status.md`
- Modify: `skills/spec-reviewer/SKILL.md`
- Modify: `skills/plan-reviewer/SKILL.md`
- Modify: `skills/impl-reviewer/SKILL.md`
- Modify: `tests/unit/test_model_effort_frontmatter.py`

- [ ] **Step 1: Write failing tests (RED)**

  Create `tests/unit/test_model_effort_frontmatter.py` with a helper and the first test class:

  ```python
  # tests/unit/test_model_effort_frontmatter.py

  import re
  import yaml
  from pathlib import Path

  REPO_ROOT = Path(__file__).parent.parent.parent

  def parse_frontmatter(rel_path: str) -> dict:
      """Extract and parse YAML frontmatter from a markdown file.

      Returns the parsed dict. Raises AssertionError if no frontmatter block
      is found, or yaml.YAMLError if the block is malformed.
      """
      text = (REPO_ROOT / rel_path).read_text()
      match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
      assert match, f"No frontmatter block found in {rel_path}"
      return yaml.safe_load(match.group(1))


  class TestHaikuLowFrontmatter:
      """Task 1 — model:haiku + effort:low on reviewer skills and zie-status."""

      def test_zie_status_model_haiku(self):
          fm = parse_frontmatter("commands/zie-status.md")
          assert fm.get("model") == "haiku", (
              "commands/zie-status.md must have model: haiku"
          )

      def test_zie_status_effort_low(self):
          fm = parse_frontmatter("commands/zie-status.md")
          assert fm.get("effort") == "low", (
              "commands/zie-status.md must have effort: low"
          )

      def test_spec_reviewer_model_haiku(self):
          fm = parse_frontmatter("skills/spec-reviewer/SKILL.md")
          assert fm.get("model") == "haiku", (
              "skills/spec-reviewer/SKILL.md must have model: haiku"
          )

      def test_spec_reviewer_effort_low(self):
          fm = parse_frontmatter("skills/spec-reviewer/SKILL.md")
          assert fm.get("effort") == "low", (
              "skills/spec-reviewer/SKILL.md must have effort: low"
          )

      def test_plan_reviewer_model_haiku(self):
          fm = parse_frontmatter("skills/plan-reviewer/SKILL.md")
          assert fm.get("model") == "haiku", (
              "skills/plan-reviewer/SKILL.md must have model: haiku"
          )

      def test_plan_reviewer_effort_low(self):
          fm = parse_frontmatter("skills/plan-reviewer/SKILL.md")
          assert fm.get("effort") == "low", (
              "skills/plan-reviewer/SKILL.md must have effort: low"
          )

      def test_impl_reviewer_model_haiku(self):
          fm = parse_frontmatter("skills/impl-reviewer/SKILL.md")
          assert fm.get("model") == "haiku", (
              "skills/impl-reviewer/SKILL.md must have model: haiku"
          )

      def test_impl_reviewer_effort_low(self):
          fm = parse_frontmatter("skills/impl-reviewer/SKILL.md")
          assert fm.get("effort") == "low", (
              "skills/impl-reviewer/SKILL.md must have effort: low"
          )
  ```

  Run: `make test-unit` — must FAIL (keys absent from all four files)

- [ ] **Step 2: Implement (GREEN)**

  Edit `commands/zie-status.md` — extend existing frontmatter block:

  ```yaml
  ---
  description: Show current SDLC state — active feature, ROADMAP summary, test health, and next suggested command.
  allowed-tools: Read, Bash, Glob
  model: haiku
  effort: low
  ---
  ```

  Edit `skills/spec-reviewer/SKILL.md` — extend existing frontmatter block:

  ```yaml
  ---
  name: spec-reviewer
  description: Review a design spec for completeness, clarity, and YAGNI. Returns APPROVED or Issues Found with specific feedback.
  model: haiku
  effort: low
  ---
  ```

  Edit `skills/plan-reviewer/SKILL.md` — extend existing frontmatter block:

  ```yaml
  ---
  name: plan-reviewer
  description: Review an implementation plan for completeness, TDD structure, and task granularity. Returns APPROVED or Issues Found with specific feedback.
  model: haiku
  effort: low
  ---
  ```

  Edit `skills/impl-reviewer/SKILL.md` — extend existing frontmatter block:

  ```yaml
  ---
  name: impl-reviewer
  description: Review a completed task implementation against its acceptance criteria. Returns APPROVED or Issues Found with specific feedback.
  model: haiku
  effort: low
  ---
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Confirm the four files' body content (all text after the closing `---`) is byte-for-byte unchanged — no line shifts, no whitespace edits. Re-read each file and diff against the pre-task snapshot.

  Run: `make test-unit` — still PASS

---

## Task 2: Add model:sonnet + effort:high to spec-design and write-plan

<!-- depends_on: none -->

**Acceptance Criteria:**
- `skills/spec-design/SKILL.md` frontmatter contains `model: sonnet` and `effort: high`
- `skills/write-plan/SKILL.md` frontmatter contains `model: sonnet` and `effort: high`
- `commands/zie-spec.md` frontmatter contains `effort: high`
- `commands/zie-plan.md` frontmatter contains `effort: high`
- All four files parse as valid YAML in the frontmatter block
- No existing content, checklist, or tool allowlist in any file is modified

**Files:**
- Modify: `skills/spec-design/SKILL.md`
- Modify: `skills/write-plan/SKILL.md`
- Modify: `commands/zie-spec.md`
- Modify: `commands/zie-plan.md`
- Modify: `tests/unit/test_model_effort_frontmatter.py`

- [ ] **Step 1: Write failing tests (RED)**

  Append `TestSonnetHighFrontmatter` class to `tests/unit/test_model_effort_frontmatter.py`:

  ```python
  class TestSonnetHighFrontmatter:
      """Task 2 — model:sonnet + effort:high on spec-design, write-plan, zie-spec, zie-plan."""

      def test_spec_design_model_sonnet(self):
          fm = parse_frontmatter("skills/spec-design/SKILL.md")
          assert fm.get("model") == "sonnet", (
              "skills/spec-design/SKILL.md must have model: sonnet"
          )

      def test_spec_design_effort_high(self):
          fm = parse_frontmatter("skills/spec-design/SKILL.md")
          assert fm.get("effort") == "high", (
              "skills/spec-design/SKILL.md must have effort: high"
          )

      def test_write_plan_model_sonnet(self):
          fm = parse_frontmatter("skills/write-plan/SKILL.md")
          assert fm.get("model") == "sonnet", (
              "skills/write-plan/SKILL.md must have model: sonnet"
          )

      def test_write_plan_effort_high(self):
          fm = parse_frontmatter("skills/write-plan/SKILL.md")
          assert fm.get("effort") == "high", (
              "skills/write-plan/SKILL.md must have effort: high"
          )

      def test_zie_spec_effort_high(self):
          fm = parse_frontmatter("commands/zie-spec.md")
          assert fm.get("effort") == "high", (
              "commands/zie-spec.md must have effort: high"
          )

      def test_zie_plan_effort_high(self):
          fm = parse_frontmatter("commands/zie-plan.md")
          assert fm.get("effort") == "high", (
              "commands/zie-plan.md must have effort: high"
          )
  ```

  Run: `make test-unit` — must FAIL (`model` and `effort` keys absent)

- [ ] **Step 2: Implement (GREEN)**

  Edit `skills/spec-design/SKILL.md` — extend existing frontmatter block:

  ```yaml
  ---
  name: spec-design
  description: Brainstorm and write a design spec for a new feature. Saves to zie-framework/specs/.
  metadata:
    zie_memory_enabled: true
  model: sonnet
  effort: high
  ---
  ```

  Edit `skills/write-plan/SKILL.md` — extend existing frontmatter block:

  ```yaml
  ---
  name: write-plan
  description: Write a detailed implementation plan from an approved spec. Saves to zie-framework/plans/.
  metadata:
    zie_memory_enabled: true
  model: sonnet
  effort: high
  ---
  ```

  Edit `commands/zie-spec.md` — extend existing frontmatter block:

  ```yaml
  ---
  description: Turn a backlog item into a written spec with Acceptance Criteria. Second stage of the SDLC pipeline.
  argument-hint: "[slug|\"idea\"] — backlog slug or inline idea string (e.g. zie-spec add-csv-export OR zie-spec \"add rate limiting\")"
  allowed-tools: Read, Write, Edit, Glob, Skill
  effort: high
  ---
  ```

  Edit `commands/zie-plan.md` — extend existing frontmatter block:

  ```yaml
  ---
  description: Plan a backlog item — draft implementation plan, present for approval, move to Ready lane.
  argument-hint: "[slug...] — one or more backlog item slugs (e.g. zie-plan feature-x feature-y)"
  allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill, Agent, TaskCreate
  effort: high
  ---
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Confirm the four files' body content is byte-for-byte unchanged after the closing `---`. Verify no `effort: high` duplication if the frontmatter-hardening spec was partially applied ahead of this plan (idempotent — same key, same value, no error).

  Run: `make test-unit` — still PASS

---

## Task 3: Add effort:medium to zie-implement and zie-fix

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-implement.md` frontmatter contains `effort: medium`
- `commands/zie-fix.md` frontmatter contains `effort: medium`
- Neither file has a `model` key added (no model pin for these commands per spec)
- Both files parse as valid YAML in the frontmatter block
- No existing content, logic, or tool allowlist in either file is modified

**Files:**
- Modify: `commands/zie-implement.md`
- Modify: `commands/zie-fix.md`
- Modify: `tests/unit/test_model_effort_frontmatter.py`

- [ ] **Step 1: Write failing tests (RED)**

  Append `TestMediumFrontmatter` class to `tests/unit/test_model_effort_frontmatter.py`:

  ```python
  class TestMediumFrontmatter:
      """Task 3 — effort:medium on zie-implement and zie-fix."""

      def test_zie_implement_effort_medium(self):
          fm = parse_frontmatter("commands/zie-implement.md")
          assert fm.get("effort") == "medium", (
              "commands/zie-implement.md must have effort: medium"
          )

      def test_zie_implement_no_model_pin(self):
          fm = parse_frontmatter("commands/zie-implement.md")
          assert "model" not in fm, (
              "commands/zie-implement.md must not have a model pin (session default)"
          )

      def test_zie_fix_effort_medium(self):
          fm = parse_frontmatter("commands/zie-fix.md")
          assert fm.get("effort") == "medium", (
              "commands/zie-fix.md must have effort: medium"
          )

      def test_zie_fix_no_model_pin(self):
          fm = parse_frontmatter("commands/zie-fix.md")
          assert "model" not in fm, (
              "commands/zie-fix.md must not have a model pin (session default)"
          )
  ```

  Run: `make test-unit` — must FAIL (`effort` key absent from both files)

- [ ] **Step 2: Implement (GREEN)**

  Edit `commands/zie-implement.md` — extend existing frontmatter block:

  ```yaml
  ---
  description: Implement the active feature using TDD — RED/GREEN/REFACTOR loop per task. Reads active plan from ROADMAP.md.
  allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill, TaskCreate, TaskUpdate
  effort: medium
  ---
  ```

  Edit `commands/zie-fix.md` — extend existing frontmatter block:

  ```yaml
  ---
  description: Debug path — skip ideation, go straight to systematic bug investigation and fix.
  argument-hint: Optional bug description or error message
  allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill
  effort: medium
  ---
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Confirm body content of both files is byte-for-byte unchanged. Verify `zie-implement.md` still contains `Skill(zie-framework:tdd-loop)` and `zie-fix.md` still contains `Skill(zie-framework:debug)` — existing test suite in `test_fork_superpowers_skills.py` covers this automatically.

  Run: `make test-unit` — still PASS

---

## Task 4: Add frontmatter parse tests — completeness and YAML validity sweep

<!-- depends_on: Task 1, Task 2, Task 3 -->

**Acceptance Criteria:**
- A `TestFrontmatterValidity` class confirms that every file modified in Tasks 1–3 has a parseable YAML frontmatter block (no malformed YAML survives)
- A `TestUnchangedSkillsHaveNoModelPin` class confirms that skills explicitly listed as "No change" in the spec (`tdd-loop`, `debug`, `retro-format`, `test-pyramid`, `verify`) do not gain accidental `model` or `effort` keys
- All new test classes are in `tests/unit/test_model_effort_frontmatter.py`
- Full `make test-unit` run passes with zero failures

**Files:**
- Modify: `tests/unit/test_model_effort_frontmatter.py`

- [ ] **Step 1: Write failing tests (RED)**

  Append the two final classes to `tests/unit/test_model_effort_frontmatter.py`:

  ```python
  class TestFrontmatterValidity:
      """Task 4 — YAML parse guard: all 10 modified files must have valid frontmatter."""

      MODIFIED_FILES = [
          "commands/zie-status.md",
          "skills/spec-reviewer/SKILL.md",
          "skills/plan-reviewer/SKILL.md",
          "skills/impl-reviewer/SKILL.md",
          "skills/spec-design/SKILL.md",
          "skills/write-plan/SKILL.md",
          "commands/zie-spec.md",
          "commands/zie-plan.md",
          "commands/zie-implement.md",
          "commands/zie-fix.md",
      ]

      def test_all_modified_files_have_valid_frontmatter(self):
          errors = []
          for rel_path in self.MODIFIED_FILES:
              try:
                  parse_frontmatter(rel_path)
              except Exception as exc:
                  errors.append(f"{rel_path}: {exc}")
          assert errors == [], "Frontmatter parse errors:\n" + "\n".join(errors)

      def test_all_modified_files_have_effort_key(self):
          errors = []
          for rel_path in self.MODIFIED_FILES:
              fm = parse_frontmatter(rel_path)
              if "effort" not in fm:
                  errors.append(rel_path)
          assert errors == [], f"Missing 'effort' key in: {errors}"

      def test_effort_values_are_valid(self):
          valid = {"low", "medium", "high"}
          errors = []
          for rel_path in self.MODIFIED_FILES:
              fm = parse_frontmatter(rel_path)
              val = fm.get("effort")
              if val not in valid:
                  errors.append(f"{rel_path}: effort={val!r}")
          assert errors == [], f"Invalid effort values: {errors}"

      def test_model_values_are_valid_when_present(self):
          valid = {"haiku", "sonnet"}
          errors = []
          for rel_path in self.MODIFIED_FILES:
              fm = parse_frontmatter(rel_path)
              val = fm.get("model")
              if val is not None and val not in valid:
                  errors.append(f"{rel_path}: model={val!r}")
          assert errors == [], f"Invalid model values: {errors}"


  class TestUnchangedSkillsHaveNoModelPin:
      """Task 4 — regression guard: skills marked 'No change' must not gain model/effort keys."""

      NO_CHANGE_SKILLS = [
          "skills/tdd-loop/SKILL.md",
          "skills/debug/SKILL.md",
          "skills/retro-format/SKILL.md",
          "skills/test-pyramid/SKILL.md",
          "skills/verify/SKILL.md",
      ]

      def test_no_change_skills_have_no_model_key(self):
          for rel_path in self.NO_CHANGE_SKILLS:
              path = REPO_ROOT / rel_path
              if not path.exists():
                  continue  # skill may not have frontmatter at all — safe to skip
              text = path.read_text()
              match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
              if not match:
                  continue  # no frontmatter block — fine
              fm = yaml.safe_load(match.group(1)) or {}
              assert "model" not in fm, (
                  f"{rel_path} must not have a model pin (out-of-scope per spec)"
              )

      def test_no_change_skills_have_no_effort_key(self):
          for rel_path in self.NO_CHANGE_SKILLS:
              path = REPO_ROOT / rel_path
              if not path.exists():
                  continue
              text = path.read_text()
              match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
              if not match:
                  continue
              fm = yaml.safe_load(match.group(1)) or {}
              assert "effort" not in fm, (
                  f"{rel_path} must not have an effort key (out-of-scope per spec)"
              )
  ```

  Run: `make test-unit` — `TestFrontmatterValidity` tests PASS (Tasks 1–3 already done); `TestUnchangedSkillsHaveNoModelPin` tests PASS immediately (no accidental edits). This is the expected GREEN state — the RED signal for Task 4 is that the test file does not yet exist before Task 1 creates it, and these final classes serve as a completeness regression net.

  If any `TestFrontmatterValidity` test fails here it means a Task 1–3 file was not edited correctly — fix the relevant frontmatter before proceeding.

- [ ] **Step 2: Implement (GREEN)**

  No implementation code needed for Task 4 — it is a pure test-completeness task. Confirm `make test-unit` exits 0 with all classes passing.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Consolidate the `parse_frontmatter` helper to the top of the file (already done in Step 1 structure above). Confirm no duplicate helper definitions exist. Verify total test count in `test_model_effort_frontmatter.py` is reasonable and each class has a clear docstring.

  Run: `make test-unit` — still PASS

---

*Commit: `git add commands/zie-status.md skills/spec-reviewer/SKILL.md skills/plan-reviewer/SKILL.md skills/impl-reviewer/SKILL.md skills/spec-design/SKILL.md skills/write-plan/SKILL.md commands/zie-spec.md commands/zie-plan.md commands/zie-implement.md commands/zie-fix.md tests/unit/test_model_effort_frontmatter.py && git commit -m "feat: model:haiku + effort routing for fast/status skills"`*
