---
approved: true
approved_at: 2026-03-24
backlog: backlog/agent-worktree-isolation.md
spec: specs/2026-03-24-agent-worktree-isolation-design.md
---

# Agent isolation:worktree + background:true Parallel Review — Implementation Plan

**Goal:** Add `isolation: worktree` to `spec-reviewer` and `plan-reviewer` agent files so those agents always read the clean committed snapshot, add `background: true` to `impl-reviewer` so it runs asynchronously during the REFACTOR phase, and update `/zie-implement` to handle the deferred-check protocol for async reviewer results.

**Architecture:** Three agent SKILL files gain new frontmatter fields. `/zie-implement` replaces the inline blocking `impl-reviewer` invocation with an async spawn + deferred-check loop. No new Python hooks, no new test infra — all changes are markdown and one command file. The spec-design and write-plan skills already invoke reviewers synchronously; those call sites are unchanged.

**Tech Stack:** Python 3.x (no new code), pytest (existing suite must stay green), Markdown agent/skill files

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `agents/spec-reviewer.md` | Agent wrapper with `isolation: worktree`; delegates to `Skill(zie-framework:spec-reviewer)` |
| Create | `agents/plan-reviewer.md` | Agent wrapper with `isolation: worktree`; delegates to `Skill(zie-framework:plan-reviewer)` |
| Create | `agents/impl-reviewer.md` | Agent wrapper with `background: true`; delegates to `Skill(zie-framework:impl-reviewer)` |
| Modify | `commands/zie-implement.md` | Replace inline blocking `impl-reviewer` invocation with async spawn + deferred-check protocol |
| Modify | `zie-framework/project/components.md` | Document Agents section with worktree and background fields |

---

## Task 1: Add isolation:worktree to spec-reviewer and plan-reviewer agent files

<!-- depends_on: none -->

**Acceptance Criteria:**
- `agents/spec-reviewer.md` exists with `isolation: worktree` in frontmatter
- `agents/plan-reviewer.md` exists with `isolation: worktree` in frontmatter
- Both agent files include the correct `allowed-tools` matching their SKILL.md (`Read`, `Glob`, `Grep`)
- Both agent files delegate execution to their corresponding `Skill(zie-framework:*)` call
- Existing unit tests continue to pass (`make test-unit`)

**Files:**
- Create: `agents/spec-reviewer.md`
- Create: `agents/plan-reviewer.md`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_agent_files.py — new file

  import re
  from pathlib import Path

  AGENTS_DIR = Path(__file__).parent.parent / "agents"

  def _read_frontmatter(path: Path) -> str:
      """Return the raw frontmatter block (between first two --- lines)."""
      text = path.read_text()
      parts = text.split("---")
      assert len(parts) >= 3, f"{path.name}: no frontmatter found"
      return parts[1]

  class TestSpecReviewerAgent:
      def test_file_exists(self):
          assert (AGENTS_DIR / "spec-reviewer.md").exists()

      def test_has_isolation_worktree(self):
          fm = _read_frontmatter(AGENTS_DIR / "spec-reviewer.md")
          assert "isolation: worktree" in fm, \
              "spec-reviewer.md must declare isolation: worktree"

      def test_has_allowed_tools(self):
          fm = _read_frontmatter(AGENTS_DIR / "spec-reviewer.md")
          assert "allowed-tools:" in fm

      def test_delegates_to_skill(self):
          text = (AGENTS_DIR / "spec-reviewer.md").read_text()
          assert "Skill(zie-framework:spec-reviewer)" in text

  class TestPlanReviewerAgent:
      def test_file_exists(self):
          assert (AGENTS_DIR / "plan-reviewer.md").exists()

      def test_has_isolation_worktree(self):
          fm = _read_frontmatter(AGENTS_DIR / "plan-reviewer.md")
          assert "isolation: worktree" in fm, \
              "plan-reviewer.md must declare isolation: worktree"

      def test_has_allowed_tools(self):
          fm = _read_frontmatter(AGENTS_DIR / "plan-reviewer.md")
          assert "allowed-tools:" in fm

      def test_delegates_to_skill(self):
          text = (AGENTS_DIR / "plan-reviewer.md").read_text()
          assert "Skill(zie-framework:plan-reviewer)" in text
  ```

  Run: `make test-unit` — must FAIL (`agents/` directory and files do not exist yet)

- [ ] **Step 2: Implement (GREEN)**

  Create `agents/spec-reviewer.md`:

  ```markdown
  ---
  description: Review a design spec for completeness, clarity, and YAGNI. Returns APPROVED or Issues Found with specific feedback.
  isolation: worktree
  allowed-tools: Read, Glob, Grep
  ---

  # spec-reviewer agent

  Invoke `Skill(zie-framework:spec-reviewer)` with the spec path and backlog context
  provided by the caller.
  ```

  Create `agents/plan-reviewer.md`:

  ```markdown
  ---
  description: Review an implementation plan for completeness, TDD structure, and task granularity. Returns APPROVED or Issues Found with specific feedback.
  isolation: worktree
  allowed-tools: Read, Glob, Grep
  ---

  # plan-reviewer agent

  Invoke `Skill(zie-framework:plan-reviewer)` with the plan path and spec path
  provided by the caller.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Confirm neither file has stray trailing whitespace or a `background:` field
  (isolation-only agents are synchronous by design). Confirm `allowed-tools`
  lists only read-side tools — no `Write`, `Edit`, or `Bash`.

  Run: `make test-unit` — still PASS

---

## Task 2: Add background:true to impl-reviewer agent file

<!-- depends_on: none -->

**Acceptance Criteria:**
- `agents/impl-reviewer.md` exists with `background: true` in frontmatter
- The agent does NOT have `isolation: worktree` (must read live post-REFACTOR files and run `make test*`)
- `allowed-tools` includes `Read`, `Glob`, `Grep`, `Bash` (for `make test*`)
- Agent file delegates to `Skill(zie-framework:impl-reviewer)`
- Existing unit tests continue to pass (`make test-unit`)

**Files:**
- Create: `agents/impl-reviewer.md`
- Modify: `tests/unit/test_agent_files.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_agent_files.py — append to existing file

  class TestImplReviewerAgent:
      def test_file_exists(self):
          assert (AGENTS_DIR / "impl-reviewer.md").exists()

      def test_has_background_true(self):
          fm = _read_frontmatter(AGENTS_DIR / "impl-reviewer.md")
          assert "background: true" in fm, \
              "impl-reviewer.md must declare background: true"

      def test_no_isolation_worktree(self):
          fm = _read_frontmatter(AGENTS_DIR / "impl-reviewer.md")
          assert "isolation: worktree" not in fm, \
              "impl-reviewer must NOT have isolation: worktree — it needs live files"

      def test_has_bash_in_allowed_tools(self):
          fm = _read_frontmatter(AGENTS_DIR / "impl-reviewer.md")
          assert "Bash" in fm, \
              "impl-reviewer must allow Bash to run make test*"

      def test_delegates_to_skill(self):
          text = (AGENTS_DIR / "impl-reviewer.md").read_text()
          assert "Skill(zie-framework:impl-reviewer)" in text
  ```

  Run: `make test-unit` — must FAIL (`agents/impl-reviewer.md` does not exist yet)

- [ ] **Step 2: Implement (GREEN)**

  Create `agents/impl-reviewer.md`:

  ```markdown
  ---
  description: Review a completed task implementation against its acceptance criteria. Returns APPROVED or Issues Found with specific feedback.
  background: true
  allowed-tools: Read, Glob, Grep, Bash
  ---

  # impl-reviewer agent

  Invoke `Skill(zie-framework:impl-reviewer)` with the task description, Acceptance
  Criteria, and list of files changed provided by the caller.

  ## Bash tool scope

  The `Bash` tool is permitted exclusively for `make test*` commands — to verify
  the test suite state as part of the Phase 2 AC coverage check. No other shell
  commands are needed.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Confirm there is no `isolation: worktree` line anywhere in `impl-reviewer.md`
  (a stray line here would be a correctness bug, not style). Confirm the `Bash`
  scope note is clear — it should explain the narrow permitted use, not a broad
  shell grant.

  Run: `make test-unit` — still PASS

---

## Task 3: Update zie-implement command for deferred-check protocol

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- Step 6 of the task loop in `commands/zie-implement.md` invokes `@agent-impl-reviewer` with `background: true` instead of the inline `Skill(zie-framework:impl-reviewer)` call
- After spawning, `/zie-implement` records the background job handle + task ID and proceeds to the next task without blocking
- At the start of each subsequent task loop iteration, `/zie-implement` checks the pending reviewer result (`reviewer_status: pending | approved | issues_found`)
- On `issues_found`: halts, surfaces feedback, fixes inline, re-invokes reviewer synchronously; max 3 total iterations (background spawn = iteration 1)
- After the final task, `/zie-implement` waits for any still-pending background reviewer before running `make test-unit` + `Skill(zie-framework:verify)`
- If the background reviewer has not returned after 120s, surfaces: "impl-reviewer did not return — review manually before committing."
- Existing pre-task-loop preflight checks (ROADMAP, git status, `.config`, memory) are unchanged
- `make test-unit` continues to pass

**Files:**
- Modify: `commands/zie-implement.md`
- Modify: `tests/unit/test_agent_files.md` (add command content assertions)

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_agent_files.py — append to existing file

  COMMANDS_DIR = Path(__file__).parent.parent / "commands"

  class TestZieImplementCommand:
      def _read_command(self):
          return (COMMANDS_DIR / "zie-implement.md").read_text()

      def test_spawns_background_agent(self):
          text = self._read_command()
          assert "@agent-impl-reviewer" in text, \
              "zie-implement must invoke @agent-impl-reviewer (agent file, not skill)"

      def test_deferred_check_protocol_present(self):
          text = self._read_command()
          assert "reviewer_status" in text, \
              "zie-implement must check reviewer_status for deferred results"

      def test_pending_approved_issues_states_covered(self):
          text = self._read_command()
          for state in ("pending", "approved", "issues_found"):
              assert state in text, \
                  f"zie-implement must handle reviewer_status: {state}"

      def test_final_wait_before_verify(self):
          text = self._read_command()
          assert "final-wait" in text or "still-pending" in text or \
                 "wait for any" in text.lower(), \
              "zie-implement must wait for pending reviewers before verify step"

      def test_120s_timeout_surfaced(self):
          text = self._read_command()
          assert "120" in text, \
              "zie-implement must surface the 120s timeout threshold"

      def test_max_3_iterations_preserved(self):
          text = self._read_command()
          assert "3" in text and "iteration" in text.lower(), \
              "zie-implement must preserve max-3-iteration gate"

      def test_no_inline_impl_reviewer_skill(self):
          text = self._read_command()
          assert "Skill(zie-framework:impl-reviewer)" not in text, \
              "inline Skill call must be replaced by @agent-impl-reviewer invocation"
  ```

  Run: `make test-unit` — must FAIL (current `zie-implement.md` uses inline `Skill(zie-framework:impl-reviewer)` and has no `@agent-impl-reviewer`, `reviewer_status`, or timeout language)

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-implement.md`, replace step 6 of the task loop (the
  `Skill(zie-framework:impl-reviewer)` block) with the following:

  ```markdown
  6. **Spawn async impl-reviewer**:
     - Invoke `@agent-impl-reviewer` (background: true):
       pass task description, **Acceptance Criteria** from plan task header,
       and list of files changed in this task.
     - Record returned handle in the pending-reviewers list:
       `{ task_id: <N>, reviewer_handle: <handle>, reviewer_status: pending }`
     - Do NOT block — proceed immediately to announce the next task.

  6a. **Deferred-check (start of each task loop iteration)**:
     - For each entry in the pending-reviewers list:
       - Poll reviewer handle → check `reviewer_status`:
         - `reviewer_status: pending` — still running; continue current task,
           check again at the next iteration.
         - `reviewer_status: approved` — clear entry from list; no action needed.
         - `reviewer_status: issues_found` — halt current task; surface reviewer
           feedback to human; apply fixes; re-run `make test-unit`; re-invoke
           `@agent-impl-reviewer` synchronously (blocking).
           Max 3 total iterations — background spawn counts as iteration 1.
           On ✅ APPROVED: clear entry from list; resume current task.
  ```

  In `commands/zie-implement.md`, replace the "เมื่อทำครบทุก task" step 1 preamble to add the final-wait:

  ```markdown
  ### เมื่อทำครบทุก task

  0. **Final-wait for still-pending reviewers**:
     - If the pending-reviewers list is non-empty, wait for each background
       reviewer to return before proceeding.
     - If any reviewer has not returned after 120s:
       surface: "impl-reviewer did not return — review manually before committing."
       and stop. Do not commit until all reviewers have returned or Zie explicitly
       acknowledges the outstanding review.
     - Apply the same `issues_found` fix-iterate loop as step 6a above.

  1. Run full test suite: `make test-unit` (required) + `make test-int` (if available).
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read the updated `commands/zie-implement.md` end-to-end and verify:
  - The deferred-check block (6a) is clearly positioned as a loop header — it
    runs at the TOP of each iteration, before "Announce task".
  - The final-wait step is numbered `0` under "เมื่อทำครบทุก task" so it precedes
    the test run.
  - The `Skill(zie-framework:impl-reviewer)` string is completely absent from
    the file.
  - Language is consistent: `@agent-impl-reviewer` (not `agent-impl-reviewer`
    or `Agent(impl-reviewer)`).

  Run: `make test-unit` — still PASS

---

## Task 4: Update components.md — document Agents section

<!-- depends_on: Task 1, Task 2 -->

**Acceptance Criteria:**
- `zie-framework/project/components.md` contains an **Agents** section
- The section documents all three agent files: `spec-reviewer.md`, `plan-reviewer.md`, `impl-reviewer.md`
- The section explains `isolation: worktree` and `background: true` fields
- `make test-unit` continues to pass

**Files:**
- Modify: `zie-framework/project/components.md`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_agent_files.py — append to existing file

  COMPONENTS_PATH = Path(__file__).parent.parent / \
      "zie-framework" / "project" / "components.md"

  class TestComponentsDocAgents:
      def _read(self):
          return COMPONENTS_PATH.read_text()

      def test_agents_section_exists(self):
          assert "## Agents" in self._read(), \
              "components.md must have an Agents section"

      def test_spec_reviewer_documented(self):
          assert "spec-reviewer" in self._read()

      def test_plan_reviewer_documented(self):
          assert "plan-reviewer" in self._read()

      def test_impl_reviewer_documented(self):
          assert "impl-reviewer" in self._read()

      def test_isolation_worktree_explained(self):
          assert "isolation: worktree" in self._read(), \
              "components.md must explain the isolation: worktree field"

      def test_background_true_explained(self):
          assert "background: true" in self._read(), \
              "components.md must explain the background: true field"
  ```

  Run: `make test-unit` — must FAIL (`components.md` has no Agents section)

- [ ] **Step 2: Implement (GREEN)**

  Append to `zie-framework/project/components.md`:

  ```markdown
  ## Agents

  Agent files live in `agents/`. Each is a markdown file with a frontmatter block
  that controls Claude Code runtime behavior. The body instructs the agent to
  invoke the corresponding skill.

  | Agent | Frontmatter | Invoked by | Purpose |
  | --- | --- | --- | --- |
  | `agents/spec-reviewer.md` | `isolation: worktree` | `spec-design` skill | Review spec from clean committed snapshot |
  | `agents/plan-reviewer.md` | `isolation: worktree` | `write-plan` skill | Review plan from clean committed snapshot |
  | `agents/impl-reviewer.md` | `background: true` | `/zie-implement` step 6 | Review task impl asynchronously; deferred-check on next iteration |

  ### Field reference

  **`isolation: worktree`** — Claude Code spawns the agent in a temporary git
  worktree pointing to `HEAD`. The agent sees only the last committed state;
  uncommitted working-tree changes are invisible. Worktree is auto-cleaned by the
  runtime on agent exit when no files are written.

  **`background: true`** — Claude Code spawns the agent asynchronously and returns
  a handle immediately. The caller continues without blocking. The caller is
  responsible for polling the handle and handling `approved` / `issues_found`
  states. If the runtime does not support `background: true`, the agent runs
  synchronously — behavior degrades gracefully to the pre-feature state.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Confirm the new section is at the end of `components.md` (after Hooks) and
  the table columns align. No logic changes needed.

  Run: `make test-unit` — still PASS

---

*Commit: `git add agents/ commands/zie-implement.md zie-framework/project/components.md tests/unit/test_agent_files.py && git commit -m "feat: agent-worktree-isolation — isolation:worktree + background:true parallel review"`*
