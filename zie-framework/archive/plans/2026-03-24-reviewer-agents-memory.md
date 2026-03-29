---
approved: true
approved_at: 2026-03-24
backlog: backlog/reviewer-agents-memory.md
spec: specs/2026-03-24-reviewer-agents-memory-design.md
---

# Reviewer Skills → Custom Agents with Persistent Memory — Implementation Plan

**Goal:** Convert the three reviewer skills (spec-reviewer, plan-reviewer, impl-reviewer) into Claude Code custom agent files so they run in isolated context, use `model: haiku`, and accumulate review patterns across sessions via `memory: project`.
**Architecture:** Three new files under `agents/` carry the reviewer system prompts verbatim from their SKILL.md sources, plus a structured frontmatter block that declares `model: haiku`, `permissionMode: plan`, `memory: project`, and restricted tool sets. Callers (spec-design skill, zie-plan command, zie-implement command) swap `Skill(zie-framework:<reviewer>)` for `@agent-<reviewer>` with an inline fallback comment pointing back to the skill. The skill files themselves remain intact as permanent fallback.
**Tech Stack:** Markdown (agent definitions), pytest (YAML frontmatter validation)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `agents/spec-reviewer.md` | Custom agent: spec review with haiku + memory |
| Create | `agents/plan-reviewer.md` | Custom agent: plan review with haiku + memory |
| Create | `agents/impl-reviewer.md` | Custom agent: impl review with haiku + memory + Bash(make test*) |
| Create | `tests/unit/test_reviewer_agents.py` | Validate all three agent files parse + required fields present |
| Modify | `skills/spec-design/SKILL.md` | Swap Skill() invocation for @agent-spec-reviewer with fallback comment |
| Modify | `commands/zie-plan.md` | Swap Skill() invocation for @agent-plan-reviewer with fallback comment |
| Modify | `commands/zie-implement.md` | Swap Skill() invocation for @agent-impl-reviewer with fallback comment |
| Modify | `zie-framework/project/components.md` | Add Agents section to registry |

---

## Task 1: Create `agents/spec-reviewer.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `agents/spec-reviewer.md` exists
- Frontmatter parses as valid YAML with fields: `name`, `description`, `model`, `tools`, `permissionMode`, `memory`, `user-invocable`
- `model` value is `haiku`
- `memory` value is `project`
- `permissionMode` value is `plan`
- `user-invocable` value is `false`
- `tools` contains `Read`, `Grep`, `Glob`
- Body contains the Phase 1, Phase 2, Phase 3 review logic

**Files:**
- Create: `agents/spec-reviewer.md`
- Create: `tests/unit/test_reviewer_agents.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_reviewer_agents.py
  import yaml
  from pathlib import Path

  AGENTS_DIR = Path(__file__).parents[2] / "agents"

  def load_agent_frontmatter(filename: str) -> dict:
      """Parse YAML frontmatter block from an agent markdown file."""
      path = AGENTS_DIR / filename
      text = path.read_text()
      assert text.startswith("---\n"), f"{filename}: missing opening frontmatter delimiter"
      end = text.index("---\n", 4)
      return yaml.safe_load(text[4:end])


  class TestSpecReviewerAgent:
      def test_agent_file_exists(self):
          assert (AGENTS_DIR / "spec-reviewer.md").exists()

      def test_frontmatter_parses(self):
          fm = load_agent_frontmatter("spec-reviewer.md")
          assert isinstance(fm, dict)

      def test_required_fields_present(self):
          fm = load_agent_frontmatter("spec-reviewer.md")
          for field in ("name", "description", "model", "tools", "permissionMode", "memory", "user-invocable"):
              assert field in fm, f"missing field: {field}"

      def test_model_is_haiku(self):
          fm = load_agent_frontmatter("spec-reviewer.md")
          assert fm["model"] == "haiku"

      def test_memory_is_project(self):
          fm = load_agent_frontmatter("spec-reviewer.md")
          assert fm["memory"] == "project"

      def test_permission_mode_is_plan(self):
          fm = load_agent_frontmatter("spec-reviewer.md")
          assert fm["permissionMode"] == "plan"

      def test_user_invocable_is_false(self):
          fm = load_agent_frontmatter("spec-reviewer.md")
          assert fm["user-invocable"] is False

      def test_tools_contains_required(self):
          fm = load_agent_frontmatter("spec-reviewer.md")
          tools = fm["tools"]
          for t in ("Read", "Grep", "Glob"):
              assert t in tools, f"missing tool: {t}"

      def test_body_contains_phase_headings(self):
          text = (AGENTS_DIR / "spec-reviewer.md").read_text()
          assert "Phase 1" in text
          assert "Phase 2" in text
          assert "Phase 3" in text
  ```
  Run: `make test-unit` — must FAIL (`agents/spec-reviewer.md` does not exist)

- [ ] **Step 2: Implement (GREEN)**
  Create `agents/spec-reviewer.md`:
  ```markdown
  ---
  name: spec-reviewer
  description: Review a design spec for completeness, clarity, and YAGNI. Returns APPROVED or Issues Found with specific feedback.
  model: haiku
  tools: Read, Grep, Glob
  permissionMode: plan
  memory: project
  user-invocable: false
  ---

  # spec-reviewer — Design Spec Review

  Subagent reviewer for design specs. Called by `spec-design` after writing the
  spec. Returns a structured verdict.

  ## Input Expected

  Caller must provide:

  - Path to spec file (`zie-framework/specs/YYYY-MM-DD-<slug>-design.md`)
  - Backlog item context (problem statement + motivation)

  ## Phase 1 — Load Context Bundle

  Before reviewing, load the following context (skip gracefully if missing —
  never block review):

  1. **Named component files** — parse the spec's **Components** section →
     read each listed file if it exists; note "FILE NOT FOUND" if missing.
     Exception: if the spec marks a file as "Create", this is expected — note
     it but do not flag as missing.
  2. **ADRs** — read all `zie-framework/decisions/*.md`.
     If directory empty or missing → note "No ADRs found", skip ADR checks.
  3. **Design context** — read `zie-framework/project/context.md` if it
     exists. If missing → note "No context doc", skip.
  4. **ROADMAP** — read `zie-framework/ROADMAP.md`, Now + Ready + Next lanes
     only. If missing → skip ROADMAP conflict check.

  ## Phase 2 — Review Checklist

  Read the spec and check each item:

  1. **Problem** — Is the problem clearly stated in 1-3 sentences?
  2. **Approach** — Is one approach chosen with brief rationale?
  3. **Components** — Are all affected files/modules listed?
  4. **Data Flow** — Is the step-by-step flow described?
  5. **Edge Cases** — Are known edge cases listed?
  6. **Out of Scope** — Is scope explicitly bounded?
  7. **YAGNI** — Does the spec include anything not needed for the stated problem?
  8. **Ambiguity** — Are there any requirements that could be interpreted multiple
     ways without more context?
  9. **Testability** — Can acceptance criteria be derived from this spec?

  ## Phase 3 — Context Checks

  Cross-reference the spec against the loaded bundle:

  1. **File existence** — list any named component files that don't exist and
     are not marked "Create" in the spec.
  2. **ADR conflict** — flag any design decision in the spec that contradicts a
     loaded ADR. If no ADRs loaded → skip.
  3. **ROADMAP conflict** — flag if this spec overlaps a Ready or Now item
     (same feature or duplicate scope). If ROADMAP missing → skip.

  Surface Phase 3 issues in the same `Issues Found` block as Phase 2 issues.

  ## Output Format

  If all checks pass:

  ```text
  APPROVED

  Spec is complete, clear, and scoped correctly.
  ```

  If issues found:

  ```text
  Issues Found

  1. [Section] <specific issue and what to fix>
  2. [Section] <specific issue and what to fix>

  Fix these and re-submit for review.
  ```

  ## Notes

  - Be specific — don't approve vague specs
  - Be concise — don't invent requirements the user didn't ask for
  - Max 3 review iterations before surfacing to human
  - Use accumulated memory of past review patterns to calibrate thresholds
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Confirm frontmatter delimiter is `---` (no trailing spaces). Confirm body
  prose is identical to `skills/spec-reviewer/SKILL.md` Phase 1-3 content.
  Run: `make test-unit` — still PASS

---

## Task 2: Create `agents/plan-reviewer.md`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `agents/plan-reviewer.md` exists
- Frontmatter: `name=plan-reviewer`, `model=haiku`, `memory=project`, `permissionMode=plan`, `user-invocable=false`, `tools` contains `Read`, `Grep`, `Glob`
- Body contains Phase 1, Phase 2, Phase 3 headings

**Files:**
- Create: `agents/plan-reviewer.md`
- Modify: `tests/unit/test_reviewer_agents.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_reviewer_agents.py — add new class after TestSpecReviewerAgent

  class TestPlanReviewerAgent:
      def test_agent_file_exists(self):
          assert (AGENTS_DIR / "plan-reviewer.md").exists()

      def test_frontmatter_parses(self):
          fm = load_agent_frontmatter("plan-reviewer.md")
          assert isinstance(fm, dict)

      def test_required_fields_present(self):
          fm = load_agent_frontmatter("plan-reviewer.md")
          for field in ("name", "description", "model", "tools", "permissionMode", "memory", "user-invocable"):
              assert field in fm, f"missing field: {field}"

      def test_model_is_haiku(self):
          fm = load_agent_frontmatter("plan-reviewer.md")
          assert fm["model"] == "haiku"

      def test_memory_is_project(self):
          fm = load_agent_frontmatter("plan-reviewer.md")
          assert fm["memory"] == "project"

      def test_permission_mode_is_plan(self):
          fm = load_agent_frontmatter("plan-reviewer.md")
          assert fm["permissionMode"] == "plan"

      def test_user_invocable_is_false(self):
          fm = load_agent_frontmatter("plan-reviewer.md")
          assert fm["user-invocable"] is False

      def test_tools_contains_required(self):
          fm = load_agent_frontmatter("plan-reviewer.md")
          tools = fm["tools"]
          for t in ("Read", "Grep", "Glob"):
              assert t in tools, f"missing tool: {t}"

      def test_body_contains_phase_headings(self):
          text = (AGENTS_DIR / "plan-reviewer.md").read_text()
          assert "Phase 1" in text
          assert "Phase 2" in text
          assert "Phase 3" in text
  ```
  Run: `make test-unit` — must FAIL (`agents/plan-reviewer.md` does not exist)

- [ ] **Step 2: Implement (GREEN)**
  Create `agents/plan-reviewer.md`:
  ```markdown
  ---
  name: plan-reviewer
  description: Review an implementation plan for completeness, TDD structure, and task granularity. Returns APPROVED or Issues Found with specific feedback.
  model: haiku
  tools: Read, Grep, Glob
  permissionMode: plan
  memory: project
  user-invocable: false
  ---

  # plan-reviewer — Implementation Plan Review

  Subagent reviewer for implementation plans. Called by `write-plan` after
  drafting the plan. Returns a structured verdict.

  ## Input Expected

  Caller must provide:

  - Path to plan file (`zie-framework/plans/YYYY-MM-DD-<slug>.md`)
  - Path to spec file (for context on what must be implemented)

  ## Phase 1 — Load Context Bundle

  Before reviewing, load the following context (skip gracefully if missing —
  never block review):

  1. **File map files** — parse the plan's file map section → read each listed
     file if it exists; note "FILE NOT FOUND" if missing. Files marked "Create"
     are expected to not exist — note but do not flag.
  2. **ADRs** — read all `zie-framework/decisions/*.md`.
     If directory empty or missing → note "No ADRs found", skip ADR checks.
  3. **Design context** — read `zie-framework/project/context.md` if it
     exists. If missing → note "No context doc", skip.
  4. **ROADMAP** — read `zie-framework/ROADMAP.md`, Now + Ready + Next lanes
     only. If missing → skip ROADMAP conflict check.

  ## Phase 2 — Review Checklist

  Read the plan and check each item:

  1. **Header** — Does the plan have `approved: false`, `backlog:`, Goal,
     Architecture, Tech Stack?
  2. **File map** — Are all files to be created or modified listed with
     responsibilities?
  3. **TDD structure** — Does each task follow RED → GREEN → REFACTOR with
     explicit `make test-unit` steps?
  4. **Task granularity** — Is each task completable in one focused session?
     Flag tasks that try to do too much at once.
  5. **Exact paths** — Are all file paths exact (no "add to the relevant file")?
  6. **Complete code** — Does each step include actual code, not "implement X"?
  7. **Dependencies** — Are task dependencies expressed with `depends_on`
     comments where needed?
  8. **Spec coverage** — Does the plan cover every requirement in the spec?
  9. **YAGNI** — Does the plan include anything the spec doesn't require?

  ## Phase 3 — Context Checks

  1. **File existence** — list any file-map files that don't exist and are not
     marked "Create".
  2. **ADR conflict** — flag any planned approach that contradicts a loaded ADR.
     If no ADRs → skip.
  3. **ROADMAP conflict** — flag if this plan overlaps a Ready or Now item
     (same feature or duplicate scope). If ROADMAP missing → skip.
  4. **Pattern match** — flag if the planned approach diverges from patterns
     observed in the read files. Surface the divergence for Zie to accept or
     reject — reviewer notes, does not decide.

  Surface Phase 3 issues in the same `Issues Found` block as Phase 2 issues.

  ## Output Format

  If all checks pass:

  ```text
  APPROVED

  Plan is complete, TDD-structured, and covers the spec.
  ```

  If issues found:

  ```text
  Issues Found

  1. [Task N / Section] <specific issue and what to fix>
  2. [Task N / Section] <specific issue and what to fix>

  Fix these and re-submit for review.
  ```

  ## Notes

  - Reject plans with vague steps like "implement the feature" or "add tests"
  - Reject plans where TDD steps are missing `make test-unit` verification
  - Max 3 review iterations before surfacing to human
  - Use accumulated memory of past review patterns to calibrate thresholds
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Confirm body prose matches `skills/plan-reviewer/SKILL.md` Phase 1-3 content
  exactly. No additions beyond the memory note at the end.
  Run: `make test-unit` — still PASS

---

## Task 3: Create `agents/impl-reviewer.md`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `agents/impl-reviewer.md` exists
- Frontmatter: `model=haiku`, `memory=project`, `permissionMode=plan`, `user-invocable=false`
- `tools` contains `Read`, `Grep`, `Glob`, and `Bash`
- `Bash` tool is scoped to `make test*` only (expressed in frontmatter as `Bash(make test*)`)
- Body contains Phase 1, Phase 2, Phase 3 headings

**Files:**
- Create: `agents/impl-reviewer.md`
- Modify: `tests/unit/test_reviewer_agents.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_reviewer_agents.py — add new class after TestPlanReviewerAgent

  class TestImplReviewerAgent:
      def test_agent_file_exists(self):
          assert (AGENTS_DIR / "impl-reviewer.md").exists()

      def test_frontmatter_parses(self):
          fm = load_agent_frontmatter("impl-reviewer.md")
          assert isinstance(fm, dict)

      def test_required_fields_present(self):
          fm = load_agent_frontmatter("impl-reviewer.md")
          for field in ("name", "description", "model", "tools", "permissionMode", "memory", "user-invocable"):
              assert field in fm, f"missing field: {field}"

      def test_model_is_haiku(self):
          fm = load_agent_frontmatter("impl-reviewer.md")
          assert fm["model"] == "haiku"

      def test_memory_is_project(self):
          fm = load_agent_frontmatter("impl-reviewer.md")
          assert fm["memory"] == "project"

      def test_permission_mode_is_plan(self):
          fm = load_agent_frontmatter("impl-reviewer.md")
          assert fm["permissionMode"] == "plan"

      def test_user_invocable_is_false(self):
          fm = load_agent_frontmatter("impl-reviewer.md")
          assert fm["user-invocable"] is False

      def test_tools_contains_read_grep_glob(self):
          fm = load_agent_frontmatter("impl-reviewer.md")
          tools = fm["tools"]
          for t in ("Read", "Grep", "Glob"):
              assert t in tools, f"missing tool: {t}"

      def test_tools_contains_bash_scoped(self):
          fm = load_agent_frontmatter("impl-reviewer.md")
          tools = fm["tools"]
          # Bash must be present and scoped (not bare "Bash")
          assert "Bash(make test*)" in tools, \
              "impl-reviewer Bash tool must be scoped to 'make test*'"

      def test_body_contains_phase_headings(self):
          text = (AGENTS_DIR / "impl-reviewer.md").read_text()
          assert "Phase 1" in text
          assert "Phase 2" in text
          assert "Phase 3" in text
  ```
  Run: `make test-unit` — must FAIL (`agents/impl-reviewer.md` does not exist)

- [ ] **Step 2: Implement (GREEN)**
  Create `agents/impl-reviewer.md`:
  ```markdown
  ---
  name: impl-reviewer
  description: Review a completed task implementation against its acceptance criteria. Returns APPROVED or Issues Found with specific feedback.
  model: haiku
  tools: Read, Grep, Glob, Bash(make test*)
  permissionMode: plan
  memory: project
  user-invocable: false
  ---

  # impl-reviewer — Task Implementation Review

  Subagent reviewer for completed task implementations. Called by `zie-implement`
  after each REFACTOR phase. Returns a structured verdict.

  ## Input Expected

  Caller must provide:

  - Task description and Acceptance Criteria (from plan)
  - List of files changed in this task

  ## Phase 1 — Load Context Bundle

  Before reviewing, load the following context (skip gracefully if missing —
  never block review):

  1. **Modified files** — read each file listed in the caller's "files changed"
     input; note "FILE NOT FOUND" if any are missing.
  2. **ADRs** — read all `zie-framework/decisions/*.md`.
     If directory empty or missing → note "No ADRs found", skip ADR checks.
  3. **Design context** — read `zie-framework/project/context.md` if it
     exists. If missing → note "No context doc", skip.

  ## Phase 2 — Review Checklist

  Read the changed files and check each item:

  1. **AC coverage** — Does the implementation satisfy every acceptance criterion?
  2. **Tests exist** — Are there tests for the new behavior?
  3. **Tests pass** — Did `make test-unit` exit 0? (Caller confirms — reviewer
     checks logic)
  4. **No over-engineering** — Is the implementation minimal for the AC? Flag
     speculative code.
  5. **No regressions** — Do any changes break existing contracts or interfaces?
  6. **Code clarity** — Are names clear? Is logic self-evident? Flag anything
     that will confuse future readers.
  7. **Security** — Any hardcoded secrets, command injection, or SQL injection?
  8. **Dead code** — Any commented-out code or unreachable branches?

  ## Phase 3 — Context Checks

  1. **File existence** — flag any file in the changed-files list that is
     missing (may indicate incomplete implementation).
  2. **ADR compliance** — flag any implementation detail that contradicts a
     loaded ADR. If no ADRs → skip.
  3. **Pattern match** — flag if implementation diverges from patterns in the
     read files. Surface for Zie to accept or reject — reviewer notes, does
     not decide.

  Surface Phase 3 issues in the same `Issues Found` block as Phase 2 issues.

  ## Output Format

  If all checks pass:

  ```text
  APPROVED

  Implementation satisfies AC. Tests present and passing.
  ```

  If issues found:

  ```text
  Issues Found

  1. [File:line] <specific issue and what to fix>
  2. [File:line] <specific issue and what to fix>

  Fix these, re-run make test-unit, and re-invoke impl-reviewer.
  ```

  ## Notes

  - Be specific about file and line when flagging issues
  - Don't nitpick style unless it causes real confusion
  - Max 3 review iterations before surfacing to human
  - Use accumulated memory of past review patterns to calibrate thresholds
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Confirm `Bash(make test*)` scoping is correctly formatted in frontmatter.
  Confirm body matches `skills/impl-reviewer/SKILL.md` Phase 1-3 content.
  Run: `make test-unit` — still PASS

---

## Task 4: Update `skills/spec-design/SKILL.md` to reference agent

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- Step 5 in `skills/spec-design/SKILL.md` invokes `@agent-spec-reviewer` as primary path
- An inline fallback comment `<!-- fallback: Skill(zie-framework:spec-reviewer) -->` is present immediately after the invocation line
- Existing prose and all other steps are unchanged

**Files:**
- Modify: `skills/spec-design/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_reviewer_agents.py — add new class after TestImplReviewerAgent

  class TestCallerUpdates:
      def test_spec_design_skill_references_agent(self):
          text = (Path(__file__).parents[2] / "skills" / "spec-design" / "SKILL.md").read_text()
          assert "@agent-spec-reviewer" in text, \
              "spec-design SKILL.md must reference @agent-spec-reviewer"

      def test_spec_design_skill_has_fallback_comment(self):
          text = (Path(__file__).parents[2] / "skills" / "spec-design" / "SKILL.md").read_text()
          assert "fallback: Skill(zie-framework:spec-reviewer)" in text, \
              "spec-design SKILL.md must have fallback comment"
  ```
  Run: `make test-unit` — must FAIL (`@agent-spec-reviewer` not yet in file)

- [ ] **Step 2: Implement (GREEN)**
  In `skills/spec-design/SKILL.md`, replace Step 5's reviewer invocation line:

  Before:
  ```
  - Invoke `Skill(zie-framework:spec-reviewer)` with:
  ```
  After:
  ```
  - Invoke `@agent-spec-reviewer` with:
    <!-- fallback: Skill(zie-framework:spec-reviewer) -->
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Read the full step 5 block to confirm only the invocation line changed;
  all bullet sub-items and retry logic are intact.
  Run: `make test-unit` — still PASS

---

## Task 5: Update `commands/zie-plan.md` to reference agent

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- `commands/zie-plan.md` invokes `@agent-plan-reviewer` as primary path
- Inline fallback comment `<!-- fallback: Skill(zie-framework:plan-reviewer) -->` present
- All other command logic unchanged

**Files:**
- Modify: `commands/zie-plan.md`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_reviewer_agents.py — add inside TestCallerUpdates

      def test_zie_plan_command_references_agent(self):
          text = (Path(__file__).parents[2] / "commands" / "zie-plan.md").read_text()
          assert "@agent-plan-reviewer" in text, \
              "zie-plan.md must reference @agent-plan-reviewer"

      def test_zie_plan_command_has_fallback_comment(self):
          text = (Path(__file__).parents[2] / "commands" / "zie-plan.md").read_text()
          assert "fallback: Skill(zie-framework:plan-reviewer)" in text, \
              "zie-plan.md must have fallback comment"
  ```
  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**
  In `commands/zie-plan.md`, under the `## plan-reviewer gate` section,
  replace the invocation line:

  Before:
  ```
  1. Invoke `Skill(zie-framework:plan-reviewer)` with:
  ```
  After:
  ```
  1. Invoke `@agent-plan-reviewer` with:
     <!-- fallback: Skill(zie-framework:plan-reviewer) -->
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Verify the sub-bullets (path to plan file, path to spec file, retry logic,
  max 3 iterations) are untouched.
  Run: `make test-unit` — still PASS

---

## Task 6: Update `commands/zie-implement.md` to reference agent

<!-- depends_on: Task 3 -->

**Acceptance Criteria:**
- `commands/zie-implement.md` invokes `@agent-impl-reviewer` as primary path
- Inline fallback comment `<!-- fallback: Skill(zie-framework:impl-reviewer) -->` present
- All other command logic unchanged

**Files:**
- Modify: `commands/zie-implement.md`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_reviewer_agents.py — add inside TestCallerUpdates

      def test_zie_implement_command_references_agent(self):
          text = (Path(__file__).parents[2] / "commands" / "zie-implement.md").read_text()
          assert "@agent-impl-reviewer" in text, \
              "zie-implement.md must reference @agent-impl-reviewer"

      def test_zie_implement_command_has_fallback_comment(self):
          text = (Path(__file__).parents[2] / "commands" / "zie-implement.md").read_text()
          assert "fallback: Skill(zie-framework:impl-reviewer)" in text, \
              "zie-implement.md must have fallback comment"
  ```
  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**
  In `commands/zie-implement.md`, Step 6 of the task loop, replace the
  invocation line:

  Before:
  ```
  - Invoke `Skill(zie-framework:impl-reviewer)`:
  ```
  After:
  ```
  - Invoke `@agent-impl-reviewer`:
    <!-- fallback: Skill(zie-framework:impl-reviewer) -->
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Verify AC pass-through bullet, Issues Found fix loop, and max 3 iterations
  note are intact.
  Run: `make test-unit` — still PASS

---

## Task 7: Update `zie-framework/project/components.md` with Agents section

<!-- depends_on: Task 1, Task 2, Task 3 -->

**Acceptance Criteria:**
- `zie-framework/project/components.md` contains an `## Agents` section
- The section lists all three agents: `spec-reviewer`, `plan-reviewer`, `impl-reviewer`
- Each row shows: Agent name, model, memory, Invoked by
- Last updated date is updated to `2026-03-24`

**Files:**
- Modify: `zie-framework/project/components.md`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_reviewer_agents.py — add new class after TestCallerUpdates

  class TestComponentsRegistry:
      def test_agents_section_exists(self):
          text = (Path(__file__).parents[2] / "zie-framework" / "project" / "components.md").read_text()
          assert "## Agents" in text, "components.md must have an Agents section"

      def test_all_three_agents_listed(self):
          text = (Path(__file__).parents[2] / "zie-framework" / "project" / "components.md").read_text()
          for agent in ("spec-reviewer", "plan-reviewer", "impl-reviewer"):
              assert agent in text, f"components.md Agents section must list {agent}"
  ```
  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**
  Append to `zie-framework/project/components.md` after the Hooks table:

  ```markdown
  ## Agents

  | Agent | Model | Memory | Invoked by |
  | --- | --- | --- | --- |
  | spec-reviewer | haiku | project | skills/spec-design (Step 5) |
  | plan-reviewer | haiku | project | commands/zie-plan (plan-reviewer gate) |
  | impl-reviewer | haiku | project | commands/zie-implement (Step 6) |
  ```

  Also update the `**Last updated:**` line to `2026-03-24`.
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Confirm existing Commands, Skills, and Hooks tables are untouched.
  Run: `make test-unit` — still PASS

---

*Commit: `git add agents/ skills/spec-design/SKILL.md commands/zie-plan.md commands/zie-implement.md zie-framework/project/components.md tests/unit/test_reviewer_agents.py && git commit -m "feat: reviewer-agents-memory"`*
