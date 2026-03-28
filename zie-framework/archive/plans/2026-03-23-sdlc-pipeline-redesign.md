---
approved: true
approved_at: 2026-03-23
backlog: backlog/sdlc-pipeline-redesign.md
---

# SDLC Pipeline Redesign — Implementation Plan

**Goal:** Replace the current command set with a clean 6-stage pipeline
(zie-backlog, zie-spec, zie-plan, zie-implement, zie-release, zie-retro) and
add spec/plan/implementation reviewer loops as quality gates.

**Architecture:** Create new command files, create 3 reviewer skill files,
update spec-design and write-plan skills to invoke reviewer loops, update
intent-detect hook, update all tests, then delete old command files. Order
matters: new files first → tests updated → old files deleted.

**Tech Stack:** Markdown (commands, skills), Python (hooks, tests)

---

## แผนที่ไฟล์

| Action | File | Change |
| --- | --- | --- |
| Create | `tests/unit/test_sdlc_pipeline.py` | 17 tests for new structure |
| Create | `commands/zie-backlog.md` | Stage 1 command |
| Create | `commands/zie-spec.md` | Stage 2 command |
| Create | `commands/zie-implement.md` | Stage 4 (from zie-build) |
| Create | `commands/zie-release.md` | Stage 5 (from zie-ship) |
| Modify | `commands/zie-plan.md` | Input = approved spec (not raw backlog) |
| Create | `skills/spec-reviewer/SKILL.md` | Spec quality gate subagent |
| Create | `skills/plan-reviewer/SKILL.md` | Plan quality gate subagent |
| Create | `skills/impl-reviewer/SKILL.md` | Implementation quality gate |
| Modify | `skills/spec-design/SKILL.md` | Add spec-reviewer loop after draft |
| Modify | `skills/write-plan/SKILL.md` | Add plan-reviewer loop after draft |
| Modify | `commands/zie-implement.md` | Add impl-reviewer after each task |
| Modify | `hooks/intent-detect.py` | New categories + suggestions |
| Modify | `hooks/session-resume.py` | Update /zie-idea → /zie-backlog ref |
| Modify | `skills/tdd-loop/SKILL.md` | Update zie-build → zie-implement ref |
| Modify | `tests/unit/test_fork_superpowers_skills.py` | New command names |
| Modify | `tests/unit/test_sdlc_gates.py` | New command names |
| Modify | `tests/unit/test_e2e_optimization.py` | New command names |
| Modify | `tests/unit/test_branding.py` | New command names |
| Delete | `commands/zie-idea.md` | Replaced by zie-backlog + zie-spec |
| Delete | `commands/zie-build.md` | Replaced by zie-implement |
| Delete | `commands/zie-ship.md` | Replaced by zie-release |
| Modify | `CLAUDE.md` | Command references |
| Modify | `README.md` | Command table |
| Modify | `.claude-plugin/marketplace.json` | Description |
| Modify | `zie-framework/ROADMAP.md` | Header line |

---

## Task 1: Write failing tests (RED)

<!-- No depends_on -->

**Files:**

- Create: `tests/unit/test_sdlc_pipeline.py`

- [ ] **Step 1: Create test file**

  ```python
  import os

  REPO_ROOT = os.path.abspath(
      os.path.join(os.path.dirname(__file__), "..", "..")
  )


  def cmd(name):
      return os.path.join(REPO_ROOT, "commands", f"zie-{name}.md")


  def skill(name):
      return os.path.join(REPO_ROOT, "skills", name, "SKILL.md")


  def read(rel):
      with open(os.path.join(REPO_ROOT, rel)) as f:
          return f.read()


  class TestNewCommandsExist:
      def test_zie_backlog_exists(self):
          assert os.path.exists(cmd("backlog")), \
              "commands/zie-backlog.md must exist"

      def test_zie_spec_exists(self):
          assert os.path.exists(cmd("spec")), \
              "commands/zie-spec.md must exist"

      def test_zie_implement_exists(self):
          assert os.path.exists(cmd("implement")), \
              "commands/zie-implement.md must exist"

      def test_zie_release_exists(self):
          assert os.path.exists(cmd("release")), \
              "commands/zie-release.md must exist"


  class TestOldCommandsRemoved:
      def test_zie_idea_removed(self):
          assert not os.path.exists(cmd("idea")), \
              "commands/zie-idea.md must be removed (split into backlog+spec)"

      def test_zie_build_removed(self):
          assert not os.path.exists(cmd("build")), \
              "commands/zie-build.md must be removed (renamed to implement)"

      def test_zie_ship_removed(self):
          assert not os.path.exists(cmd("ship")), \
              "commands/zie-ship.md must be removed (renamed to release)"


  class TestIntentDetectUpdated:
      def _hook(self):
          return read("hooks/intent-detect.py")

      def test_has_backlog_suggestion(self):
          assert '"/zie-backlog"' in self._hook(), \
              "intent-detect must suggest /zie-backlog"

      def test_has_spec_suggestion(self):
          assert '"/zie-spec"' in self._hook(), \
              "intent-detect must suggest /zie-spec"

      def test_has_implement_suggestion(self):
          assert '"/zie-implement"' in self._hook(), \
              "intent-detect must suggest /zie-implement"

      def test_has_release_suggestion(self):
          assert '"/zie-release"' in self._hook(), \
              "intent-detect must suggest /zie-release"

      def test_no_idea_suggestion(self):
          assert '"/zie-idea"' not in self._hook(), \
              "intent-detect must not suggest /zie-idea"

      def test_no_build_suggestion(self):
          assert '"/zie-build"' not in self._hook(), \
              "intent-detect must not suggest /zie-build"

      def test_no_ship_suggestion(self):
          assert '"/zie-ship"' not in self._hook(), \
              "intent-detect must not suggest /zie-ship"


  class TestReviewerSkillsExist:
      def test_spec_reviewer_exists(self):
          assert os.path.exists(skill("spec-reviewer")), \
              "skills/spec-reviewer/SKILL.md must exist"

      def test_plan_reviewer_exists(self):
          assert os.path.exists(skill("plan-reviewer")), \
              "skills/plan-reviewer/SKILL.md must exist"

      def test_impl_reviewer_exists(self):
          assert os.path.exists(skill("impl-reviewer")), \
              "skills/impl-reviewer/SKILL.md must exist"


  class TestSkillsInvokeReviewers:
      def test_spec_design_invokes_spec_reviewer(self):
          content = read("skills/spec-design/SKILL.md")
          assert "spec-reviewer" in content, \
              "spec-design skill must invoke spec-reviewer loop"

      def test_write_plan_invokes_plan_reviewer(self):
          content = read("skills/write-plan/SKILL.md")
          assert "plan-reviewer" in content, \
              "write-plan skill must invoke plan-reviewer loop"

      def test_zie_implement_invokes_impl_reviewer(self):
          content = read("commands/zie-implement.md")
          assert "impl-reviewer" in content, \
              "zie-implement must invoke impl-reviewer after each task"
  ```

- [ ] **Step 2: Run — must FAIL**

  ```bash
  python3 -m pytest tests/unit/test_sdlc_pipeline.py -v
  ```

  Expected: 17 FAILED

- [ ] **Step 3: Commit RED tests**

  ```bash
  git add tests/unit/test_sdlc_pipeline.py
  git commit -m "test: add failing tests for SDLC pipeline redesign"
  ```

---

## Task 2: Create new command files

<!-- No depends_on -->

**Files:**

- Create: `commands/zie-backlog.md`
- Create: `commands/zie-spec.md`
- Create: `commands/zie-implement.md`
- Create: `commands/zie-release.md`

- [ ] **Step 1: Create zie-backlog.md**

  ```markdown
  ---
  description: Capture a new backlog item — problem, motivation, rough scope.
    First stage of the SDLC pipeline.
  argument-hint: Optional idea title (e.g. "add CSV export")
  allowed-tools: Read, Write, Glob
  ---

  # /zie-backlog — Capture Backlog Item

  Capture a new idea as a backlog item. No spec or plan yet — just the
  problem and motivation. Output lives in `zie-framework/backlog/`.

  ## ตรวจสอบก่อนเริ่ม

  1. Check `zie-framework/` exists → if not, tell user to run `/zie-init`
     first.
  2. Read `zie-framework/.config` → zie_memory_enabled.
  3. If `zie_memory_enabled=true`:
     - `recall project=<project> domain=<domain> tags=[backlog] limit=10`
     - Check for duplicates — warn if similar item already exists.

  ## Steps

  1. If argument provided → use as idea title. If not → ask: "What's the
     idea? (one line title)"
  2. Derive slug: lowercase, replace spaces with hyphens, strip punctuation.
  3. Write `zie-framework/backlog/<slug>.md`:

     ```markdown
     # <Idea Title>

     ## Problem

     <what problem does this solve — 1-3 sentences>

     ## Motivation

     <why this matters now — who benefits and how>

     ## Rough Scope

     <optional — what's in and out>
     ```

  4. Update `zie-framework/ROADMAP.md` Next section:
     `- [ ] <title> — [backlog](backlog/<slug>.md)`

  5. If `zie_memory_enabled=true`:
     - `remember "Backlog: <title>. Problem: <one-line>."
       tags=[backlog, <project>]`

  6. Print:

     ```text
     Backlog item added: zie-framework/backlog/<slug>.md
     ROADMAP updated → Next

     Next: /zie-spec <slug> to write the spec.
     ```

  ## ขั้นตอนถัดไป

  → `/zie-spec <slug>` — เมื่อพร้อมเขียน spec
  → `/zie-status` — ดูภาพรวม backlog

  ## Notes

  - Can be run with argument: `/zie-backlog "add CSV export"` to skip prompt
  - Safe to re-run — will warn if slug already exists
  ```

- [ ] **Step 2: Create zie-spec.md**

  ```markdown
  ---
  description: Turn a backlog item into a written spec with Acceptance
    Criteria. Second stage of the SDLC pipeline.
  argument-hint: "[slug] — backlog item slug (e.g. zie-spec add-csv-export)"
  allowed-tools: Read, Write, Glob, Skill
  ---

  # /zie-spec — Backlog → Spec

  Write a design spec for a backlog item. Invokes spec-design skill with
  reviewer loop. Output lives in `zie-framework/specs/`.

  ## ตรวจสอบก่อนเริ่ม

  1. Check `zie-framework/` exists → if not, tell user to run `/zie-init`
     first.
  2. Read `zie-framework/.config` → zie_memory_enabled.

  ## Steps

  1. If slug provided → read `zie-framework/backlog/<slug>.md`.
     If not → read ROADMAP.md Next section, list items, ask: "Which to
     spec? Enter number."
  2. Invoke `Skill(zie-framework:spec-design)` with backlog content as
     context:
     - Skill asks clarifying questions, proposes approaches, presents
       design, writes spec, runs spec-reviewer loop until approved.
     - Spec saved to `zie-framework/specs/YYYY-MM-DD-<slug>-design.md`.
  3. Print:

     ```text
     Spec written: zie-framework/specs/YYYY-MM-DD-<slug>-design.md

     Next: /zie-plan <slug> to create the implementation plan.
     ```

  ## ขั้นตอนถัดไป

  → `/zie-plan <slug>` — เมื่อ spec approved แล้ว
  → `/zie-status` — ดูภาพรวม

  ## Notes

  - Always spec-first — never skips to plan without an approved spec
  - Spec-reviewer loop runs automatically inside spec-design skill
  ```

- [ ] **Step 3: Create zie-implement.md**

  Copy content from `commands/zie-build.md` verbatim into
  `commands/zie-implement.md`, then make these changes:
  - Line 1 description: replace "zie-build" with "zie-implement"
  - Heading: `# /zie-implement — TDD Feature Implementation Loop`
  - Add impl-reviewer invocation after each task's REFACTOR phase (see
    Task 10 for exact content)
  - All "→ /zie-ship" references → "→ /zie-release"

- [ ] **Step 4: Create zie-release.md**

  Copy content from `commands/zie-ship.md` verbatim into
  `commands/zie-release.md`, then make these changes:
  - Line 1 description: replace "zie-ship" with "zie-release"
  - Heading: `# /zie-release — Release Gate → Merge dev→main → Tag`
  - All internal `/zie-ship` self-references → `/zie-release`
  - All "→ /zie-build" references → "→ /zie-implement"
  - `make ship` reference → `make release` (if any)
  - "Auto-run `/zie-retro`" remains unchanged

- [ ] **Step 5: Run new command tests**

  ```bash
  python3 -m pytest \
    tests/unit/test_sdlc_pipeline.py::TestNewCommandsExist -v
  ```

  Expected: 4 PASS

- [ ] **Step 6: Commit**

  ```bash
  git add commands/zie-backlog.md commands/zie-spec.md \
    commands/zie-implement.md commands/zie-release.md
  git commit -m "feat: add zie-backlog, zie-spec, zie-implement, zie-release commands"
  ```

---

## Task 3: Update zie-plan.md

<!-- No depends_on -->

**Files:**

- Modify: `commands/zie-plan.md`

- [ ] **Step 1: Update pre-flight step 2**

  Change:

  ```text
  2. Read `zie-framework/.config` → zie_memory_enabled, superpowers_enabled.
  ```

  To:

  ```text
  2. Read `zie-framework/.config` → zie_memory_enabled.
  ```

  _(Note: superpowers_enabled already removed in remove-superpowers task.
  Verify it's already done — if so, skip this step.)_

- [ ] **Step 2: Update "no argument" flow**

  Change the "no argument" list to show items that have an approved spec
  (spec file exists in `zie-framework/specs/`) instead of raw Next items.
  Items without a spec should prompt: "Run /zie-spec <slug> first."

- [ ] **Step 3: Update handoff references**

  Replace any `/zie-build` references in output/notes with `/zie-implement`.

- [ ] **Step 4: Run all tests**

  ```bash
  make test-unit
  ```

  Expected: all existing tests PASS (note: old command file tests will break
  later when old files are deleted — that's handled in Task 7)

- [ ] **Step 5: Commit**

  ```bash
  git add commands/zie-plan.md
  git commit -m "feat: update zie-plan to take approved spec as input"
  ```

---

## Task 4: Create reviewer skills

<!-- No depends_on -->

**Files:**

- Create: `skills/spec-reviewer/SKILL.md`
- Create: `skills/plan-reviewer/SKILL.md`
- Create: `skills/impl-reviewer/SKILL.md`

- [ ] **Step 1: Create spec-reviewer/SKILL.md**

  ```markdown
  ---
  name: spec-reviewer
  description: Review a draft spec for completeness, clear AC, no ambiguity,
    and feasibility. Returns APPROVED or issues list.
  ---

  # spec-reviewer — Spec Quality Gate

  You are a spec reviewer. Read the spec provided and check every item
  below. Return either APPROVED or a numbered issues list. Be specific —
  point to exact sections that need fixing.

  ## Checklist

  1. **Problem clearly stated** — one sentence, specific and testable
  2. **Acceptance Criteria** — every requirement is testable, not vague
  3. **No ambiguity** — no "TBD", "somehow", vague verbs ("handle", "manage")
  4. **Approach is feasible** — technically achievable with current stack
  5. **Scope boundary defined** — Out of Scope section present and clear
  6. **Edge cases documented** — failure paths and edge inputs covered

  ## Output Format

  If all checks pass:

  ```text
  ✅ APPROVED — spec is complete and clear.
  ```

  If issues found:

  ```text
  ❌ Issues found:
  1. [Section name] — <specific issue>
  2. [Section name] — <specific issue>
  ```

  ## Notes

  - Be specific — "AC #2 is vague" is not useful; point to exact words
  - Do not add scope — only flag what is missing or unclear
  - Max 3 review iterations before surfacing to human
  ```

- [ ] **Step 2: Create plan-reviewer/SKILL.md**

  ```markdown
  ---
  name: plan-reviewer
  description: Review a draft implementation plan for AC coverage, TDD
    structure, exact file paths, and commit discipline.
  ---

  # plan-reviewer — Plan Quality Gate

  You are a plan reviewer. Read the plan and check every item below.
  Return APPROVED or a numbered issues list with specific references.

  ## Checklist

  1. **All spec AC have tasks** — every acceptance criterion maps to ≥1 task
  2. **TDD structure** — each task has RED (failing test) → GREEN (impl) →
     REFACTOR steps
  3. **Exact file paths** — no "create the module" vagueness; full paths
  4. **Test code shown** — actual test code in plan, not described
  5. **Exact run commands** — commands with expected output
  6. **Commit per task** — each task ends with a `git commit` step
  7. **depends_on markers** — sequential tasks have `<!-- depends_on: -->` comment

  ## Output Format

  ```text
  ✅ APPROVED — plan is complete and implementable.
  ```

  or

  ```text
  ❌ Issues found:
  1. Task N — <specific issue>
  2. Task N Step M — <specific issue>
  ```

  ## Notes

  - Check that file paths match what actually exists in the repo
  - A plan without test code is not a plan — flag missing test code
  - Max 3 review iterations before surfacing to human
  ```

- [ ] **Step 3: Create impl-reviewer/SKILL.md**

  ```markdown
  ---
  name: impl-reviewer
  description: Review code changes after a task — check AC met, no bugs,
    code quality, optimization. Used by /zie-implement after each task.
  ---

  # impl-reviewer — Implementation Quality Gate

  You are a code reviewer. Given a task description and the changes made,
  check every item below. Return APPROVED or a numbered issues list.

  ## Input

  - Task description (from plan)
  - Acceptance criteria for this task
  - Files changed (or git diff)

  ## Checklist

  1. **AC met** — all acceptance criteria for this task are satisfied
  2. **No bugs** — no logic errors, off-by-one, missing error handling at
     system boundaries
  3. **Code quality** — naming is clear, no duplication, follows existing
     patterns in the codebase
  4. **No over-engineering** — no code beyond what this task required (YAGNI)
  5. **Tests pass** — `make test-unit` output shows all green
  6. **No TODOs** — no placeholder comments (`TODO`, `FIXME`, `PLACEHOLDER`)
     remaining in new code

  ## Output Format

  ```text
  ✅ APPROVED — task complete and clean.
  ```

  or

  ```text
  ❌ Issues found:
  1. <file:line> — <specific issue>
  2. <file:line> — <specific issue>
  ```

  ## Notes

  - Fix → re-run `make test-unit` → re-invoke impl-reviewer until APPROVED
  - Max 3 iterations before surfacing to human
  - Do not expand scope — flag scope creep as an issue
  ```

- [ ] **Step 4: Run reviewer skill tests**

  ```bash
  python3 -m pytest \
    tests/unit/test_sdlc_pipeline.py::TestReviewerSkillsExist -v
  ```

  Expected: 3 PASS

- [ ] **Step 5: Commit**

  ```bash
  git add skills/spec-reviewer/SKILL.md skills/plan-reviewer/SKILL.md \
    skills/impl-reviewer/SKILL.md
  git commit -m "feat: add spec-reviewer, plan-reviewer, impl-reviewer skills"
  ```

---

## Task 5: Update spec-design and write-plan skills with reviewer loops

<!-- depends_on: Task 4 -->

**Files:**

- Modify: `skills/spec-design/SKILL.md`
- Modify: `skills/write-plan/SKILL.md`

- [ ] **Step 1: Add reviewer loop to spec-design**

  After step 4 ("Write spec to file"), add:

  ```markdown
  5. **Reviewer loop** — invoke `Skill(zie-framework:spec-reviewer)` as a
     subagent:
     - Pass: full spec content
     - If ❌ Issues found → fix spec → re-invoke → repeat
     - Max 3 iterations → if still issues, surface to human with issue list
     - ✅ APPROVED → proceed

  6. Ask user to review the written spec:
     "Spec written and approved by reviewer. Please check
     `zie-framework/specs/<filename>` and confirm before we write the plan."

  7. If approved → hand off to `Skill(zie-framework:write-plan)`.
  ```

  _(Renumber existing steps 5-6 to 6-7.)_

- [ ] **Step 2: Add reviewer loop to write-plan**

  After "Save plan to: `zie-framework/plans/...`" section, add:

  ```markdown
  ## Reviewer loop

  After saving the plan:

  1. Invoke `Skill(zie-framework:plan-reviewer)` as a subagent:
     - Pass: path to plan + path to spec
     - If ❌ Issues found → fix plan → re-invoke → repeat
     - Max 3 iterations → surface to human
     - ✅ APPROVED → proceed

  2. Ask user to review the written plan before building:
     "Plan written and approved by reviewer. Check
     `zie-framework/plans/<filename>`. Approve to move to Ready lane."
  ```

- [ ] **Step 3: Run reviewer skill-invocation tests**

  ```bash
  python3 -m pytest \
    tests/unit/test_sdlc_pipeline.py::TestSkillsInvokeReviewers \
    -k "spec_design or write_plan" -v
  ```

  Expected: 2 PASS

- [ ] **Step 4: Commit**

  ```bash
  git add skills/spec-design/SKILL.md skills/write-plan/SKILL.md
  git commit -m "feat: add spec-reviewer and plan-reviewer loops to skills"
  ```

---

## Task 6: Add impl-reviewer to zie-implement

<!-- depends_on: Task 2, Task 4 -->

**Files:**

- Modify: `commands/zie-implement.md`

- [ ] **Step 1: Add impl-reviewer invocation after REFACTOR phase**

  In the per-task loop (after step 5 REFACTOR), insert:

  ```markdown
  6. **Invoke `Skill(zie-framework:impl-reviewer)`**:
     - Pass: task description + AC from plan + list of files changed
     - If ❌ Issues found → fix → re-run `make test-unit` → re-invoke
       reviewer → repeat until ✅ APPROVED
     - Max 3 iterations → surface to human
  ```

  Renumber "บันทึก task เสร็จ" from step 6 to step 7, etc.

- [ ] **Step 2: Run impl-reviewer test**

  ```bash
  python3 -m pytest \
    tests/unit/test_sdlc_pipeline.py::TestSkillsInvokeReviewers::test_zie_implement_invokes_impl_reviewer \
    -v
  ```

  Expected: PASS

- [ ] **Step 3: Commit**

  ```bash
  git add commands/zie-implement.md
  git commit -m "feat: add impl-reviewer quality gate to zie-implement"
  ```

---

## Task 7: Update intent-detect.py and session-resume.py

<!-- No depends_on -->

**Files:**

- Modify: `hooks/intent-detect.py`
- Modify: `hooks/session-resume.py`

- [ ] **Step 1: Update PATTERNS in intent-detect.py**

  Replace `"idea"` key with `"backlog"` (same patterns, new key name).
  Add new `"spec"` key:

  ```python
  "backlog": [
      r"อยากทำ", r"อยากได้", r"อยากเพิ่ม", r"อยากสร้าง",
      r"\bidea\b", r"\bfeature\b", r"new feature", r"เพิ่ม.*feature",
      r"สร้าง.*ใหม่", r"want to (build|add|create|make)",
      r"ต้องการ", r"would like to",
  ],
  "spec": [
      r"\bspec\b", r"เขียน.*spec", r"design.*doc", r"spec.*feature",
      r"requirement", r"acceptance criteria", r"\bAC\b",
  ],
  ```

  Replace `"build"` key → `"implement"` (same patterns).
  Replace `"ship"` key → `"release"` (same patterns).

- [ ] **Step 2: Update SUGGESTIONS in intent-detect.py**

  ```python
  SUGGESTIONS = {
      "init":      "/zie-init",
      "backlog":   "/zie-backlog",
      "spec":      "/zie-spec",
      "plan":      "/zie-plan",
      "implement": "/zie-implement",
      "fix":       "/zie-fix",
      "release":   "/zie-release",
      "retro":     "/zie-retro",
      "status":    "/zie-status",
  }
  ```

- [ ] **Step 3: Update session-resume.py**

  Line 85: change `"run /zie-idea to start one"` →
  `"run /zie-backlog to start one"`

- [ ] **Step 4: Run hook tests**

  ```bash
  python3 -m pytest \
    tests/unit/test_sdlc_pipeline.py::TestIntentDetectUpdated -v
  ```

  Expected: 7 PASS

- [ ] **Step 5: Run existing session-resume tests**

  ```bash
  python3 -m pytest tests/unit/test_hooks_session_resume.py -v
  ```

  Expected: all PASS

- [ ] **Step 6: Run intent-detect tests**

  ```bash
  python3 -m pytest tests/unit/test_hooks_intent_detect.py -v
  ```

  Expected: may have failures — those tests reference old command names.
  Note which tests fail — they will be fixed in Task 8.

- [ ] **Step 7: Commit**

  ```bash
  git add hooks/intent-detect.py hooks/session-resume.py
  git commit -m "feat: update intent-detect and session-resume for new pipeline"
  ```

---

## Task 8: Update tdd-loop skill reference

<!-- No depends_on -->

**Files:**

- Modify: `skills/tdd-loop/SKILL.md`

- [ ] **Step 1: Update line 9**

  Change:

  ```text
  Use this skill during /zie-build for every task.
  ```

  To:

  ```text
  Use this skill during /zie-implement for every task.
  ```

- [ ] **Step 2: Run all tests**

  ```bash
  make test-unit
  ```

- [ ] **Step 3: Commit**

  ```bash
  git add skills/tdd-loop/SKILL.md
  git commit -m "fix: update tdd-loop skill reference to zie-implement"
  ```

---

## Task 9: Update existing tests to use new command names

<!-- depends_on: Task 2 -->

**Files:**

- Modify: `tests/unit/test_fork_superpowers_skills.py`
- Modify: `tests/unit/test_sdlc_gates.py`
- Modify: `tests/unit/test_e2e_optimization.py`
- Modify: `tests/unit/test_branding.py`
- Modify: `tests/unit/test_hooks_intent_detect.py`

- [ ] **Step 1: Update test_fork_superpowers_skills.py**

  Replace old command file references:

  | Old | New |
  | --- | --- |
  | `commands/zie-idea.md` | `commands/zie-spec.md` |
  | `commands/zie-build.md` | `commands/zie-implement.md` |
  | `commands/zie-ship.md` | `commands/zie-release.md` |

  Update assertion messages to match new names.

  Update `test_zie_idea_calls_zie_framework_write_plan`:
  - Remove (zie-spec only does spec-design, not write-plan)
  - Or rename to check zie-spec calls zie-framework:spec-design

- [ ] **Step 2: Update test_sdlc_gates.py**

  Replace all `read("commands/zie-ship.md")` → `read("commands/zie-release.md")`
  Replace all `read("commands/zie-build.md")` → `read("commands/zie-implement.md")`
  Replace all `read("commands/zie-idea.md")` → `read("commands/zie-backlog.md")`
  or `read("commands/zie-spec.md")` (based on what the test checks)

  Update assertion strings: "zie-build" → "zie-implement", etc.

- [ ] **Step 3: Update test_e2e_optimization.py**

  Same file path replacements as above. Review each assertion to ensure
  it checks the right behavior in the new command file.

- [ ] **Step 4: Update test_branding.py**

  Replace `commands/zie-build.md` → `commands/zie-implement.md`
  Replace `commands/zie-ship.md` → `commands/zie-release.md`

- [ ] **Step 5: Update test_hooks_intent_detect.py**

  Update assertions:
  - `/zie-build` → `/zie-implement`
  - `/zie-ship` → `/zie-release`
  - `/zie-idea` → `/zie-backlog`

- [ ] **Step 6: Run full test suite**

  ```bash
  make test-unit
  ```

  Expected: all PASS (old command files still exist at this point)

- [ ] **Step 7: Commit**

  ```bash
  git add tests/
  git commit -m "test: update all tests to reference new command names"
  ```

---

## Task 10: Delete old command files

<!-- depends_on: Task 9 -->

**Files:**

- Delete: `commands/zie-idea.md`
- Delete: `commands/zie-build.md`
- Delete: `commands/zie-ship.md`

- [ ] **Step 1: Delete files**

  ```bash
  rm commands/zie-idea.md commands/zie-build.md commands/zie-ship.md
  ```

- [ ] **Step 2: Run full test suite**

  ```bash
  make test-unit
  ```

  Expected: all PASS (tests already updated to use new names)
  Also: `TestOldCommandsRemoved` tests now PASS.

- [ ] **Step 3: Commit**

  ```bash
  git add -A commands/
  git commit -m "feat: remove old command files (zie-idea, zie-build, zie-ship)"
  ```

---

## Task 11: Update docs + marketplace + ROADMAP header

<!-- depends_on: Task 10 -->

**Files:**

- Modify: `CLAUDE.md`
- Modify: `README.md`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `zie-framework/ROADMAP.md`

- [ ] **Step 1: Update CLAUDE.md**

  Find command references and update:
  - "zie-idea" → "zie-backlog" / "zie-spec"
  - "zie-build" → "zie-implement"
  - "zie-ship" → "zie-release"

- [ ] **Step 2: Update README.md command table**

  Update all rows referencing old command names.

- [ ] **Step 3: Update marketplace.json description**

  ```json
  "description": "Solo developer SDLC framework — /zie-init, /zie-backlog,
  /zie-spec, /zie-plan, /zie-implement, /zie-fix, /zie-release, /zie-retro,
  /zie-resync with ambient intent detection and auto-test hooks"
  ```

- [ ] **Step 4: Update ROADMAP.md header line**

  Change:

  ```text
  > Updated by /zie-idea (Next), /zie-plan (Ready), /zie-build (Now),
  /zie-ship (Done), /zie-retro (reprioritization).
  ```

  To:

  ```text
  > Updated by /zie-backlog + /zie-spec (Next), /zie-plan (Ready),
  /zie-implement (Now), /zie-release (Done), /zie-retro (reprioritization).
  ```

- [ ] **Step 5: Run full test suite**

  ```bash
  make test-unit
  ```

  Expected: all PASS

- [ ] **Step 6: Commit**

  ```bash
  git add CLAUDE.md README.md .claude-plugin/marketplace.json \
    zie-framework/ROADMAP.md
  git commit -m "docs: update all references to new pipeline command names"
  ```

---

## Task 12: Final verify

<!-- depends_on: Task 11 -->

- [ ] **Step 1: Run full test suite**

  ```bash
  make test-unit
  ```

  Expected: all PASS, 17 new tests green

- [ ] **Step 2: Confirm no old command names remain in active code**

  ```bash
  grep -r "zie-idea\|zie-build\|zie-ship" \
    commands/ hooks/ skills/ CLAUDE.md README.md \
    .claude-plugin/ --include="*.md" --include="*.py" \
    --include="*.json" -l
  ```

  Expected: no output

- [ ] **Step 3: Confirm new pipeline commands all have correct frontmatter**

  ```bash
  head -5 commands/zie-backlog.md commands/zie-spec.md \
    commands/zie-implement.md commands/zie-release.md
  ```

  Expected: all have `description:` and `allowed-tools:` fields

- [ ] **Step 4: Invoke Skill(zie-framework:verify)**

- [ ] **Step 5: Add ADR to decisions.md**

  Add entry:

  ```markdown
  ## D-006: 6-Stage SDLC Pipeline Redesign (2026-03-23)

  **Decision:** Renamed commands to align with 6-stage pipeline:
  zie-idea → zie-backlog + zie-spec, zie-build → zie-implement,
  zie-ship → zie-release. Added spec/plan/implementation reviewer
  quality gates.

  **Context:** Original command names didn't match the SDLC stages they
  implemented. Quality gates were missing at spec and plan stages.

  **Consequence:** Every stage now has a dedicated command and an
  automated reviewer loop before proceeding to the next stage.
  ```

- [ ] **Step 6: Final commit**

  ```bash
  git add zie-framework/project/decisions.md
  git commit -m "docs: add ADR for SDLC pipeline redesign"
  ```
