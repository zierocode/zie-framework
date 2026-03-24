---
approved: false
approved_at: ~
backlog: backlog/reviewer-shared-context.md
spec: specs/2026-03-24-reviewer-shared-context-design.md
---

# Reviewer Shared Context Bundle — Implementation Plan

**Goal:** Eliminate redundant ADR + context.md reads across reviewer invocations within a single session. Load `zie-framework/decisions/*.md` and `zie-framework/project/context.md` once in `/zie-plan` and `/zie-implement`, then pass the pre-loaded content to each reviewer. Reviewers use the bundle when present and fall back to reading from disk when absent.

**Architecture:** Two callers (`commands/zie-plan.md`, `commands/zie-implement.md`) gain an upfront context-load block before the reviewer loop. Three reviewer skills (`skills/spec-reviewer/SKILL.md`, `skills/plan-reviewer/SKILL.md`, `skills/impl-reviewer/SKILL.md`) gain a conditional preamble in Phase 1: use caller-provided bundle if injected; otherwise read from disk as today. No behavioral change — same data, fewer reads.

**Tech Stack:** Markdown (command + skill definitions), pytest (Path.read_text() pattern assertions)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-plan.md` | Add context-load block before plan-reviewer gate; pass bundle in invocation |
| Modify | `commands/zie-implement.md` | Add context-load block before impl-reviewer spawn; pass bundle in invocation |
| Modify | `skills/spec-reviewer/SKILL.md` | Phase 1: use bundle if present, else read from disk |
| Modify | `skills/plan-reviewer/SKILL.md` | Phase 1: use bundle if present, else read from disk |
| Modify | `skills/impl-reviewer/SKILL.md` | Phase 1: use bundle if present, else read from disk |
| Create | `tests/unit/test_reviewer_shared_context.py` | Verify context-load block in commands; verify fallback prose in each skill |

---

## Task 1: Add context-load block to `commands/zie-plan.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-plan.md` contains a context-load block that reads `zie-framework/decisions/*.md` and `zie-framework/project/context.md` before the plan-reviewer gate
- The block is labelled with the comment `<!-- context-load: adrs + project context -->`
- The plan-reviewer invocation passes `context_bundle` as a named input
- All existing command logic (WIP check, spec filter, write-plan step, Zie approval flow) is unchanged

**Files:**
- Modify: `commands/zie-plan.md`
- Create: `tests/unit/test_reviewer_shared_context.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_reviewer_shared_context.py
  from pathlib import Path

  COMMANDS_DIR = Path(__file__).parents[2] / "commands"
  SKILLS_DIR   = Path(__file__).parents[2] / "skills"


  class TestZiePlanContextLoad:
      def test_context_load_marker_present(self):
          text = (COMMANDS_DIR / "zie-plan.md").read_text()
          assert "<!-- context-load: adrs + project context -->" in text, \
              "zie-plan.md must have context-load comment marker"

      def test_adrs_load_step_present(self):
          text = (COMMANDS_DIR / "zie-plan.md").read_text()
          assert "decisions/*.md" in text, \
              "zie-plan.md must load zie-framework/decisions/*.md"

      def test_context_md_load_step_present(self):
          text = (COMMANDS_DIR / "zie-plan.md").read_text()
          assert "project/context.md" in text, \
              "zie-plan.md must load zie-framework/project/context.md"

      def test_reviewer_invocation_passes_bundle(self):
          text = (COMMANDS_DIR / "zie-plan.md").read_text()
          assert "context_bundle" in text, \
              "zie-plan.md must pass context_bundle to reviewer invocation"
  ```

  Run: `make test-unit` — must FAIL (none of these strings exist in the file yet)

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-plan.md`, insert the following block immediately before the `## plan-reviewer gate` section:

  ```markdown
  ## โหลด context bundle (ครั้งเดียวต่อ session)

  <!-- context-load: adrs + project context -->

  Before invoking any reviewer, load shared context once:

  1. Read all `zie-framework/decisions/*.md` → store as `adrs_content`
     (list of `{filename, content}` pairs; empty list if directory missing)
  2. Read `zie-framework/project/context.md` → store as `context_content`
     (string; empty string if file missing)
  3. Bundle as `context_bundle = { adrs: adrs_content, context: context_content }`

  Pass `context_bundle` to every reviewer invocation below.
  ```

  Then in the `## plan-reviewer gate` section, update the reviewer invocation to:

  ```markdown
  1. Invoke `@agent-plan-reviewer` with:
     <!-- fallback: Skill(zie-framework:plan-reviewer) -->
     - Path to plan file
     - Path to spec file (`zie-framework/specs/*-<slug>-design.md`)
     - `context_bundle` (pre-loaded ADRs + context.md)
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read the full command file. Confirm:
  - The context-load block appears after the `## ร่าง plan` section and before `## plan-reviewer gate`
  - No existing sections were removed or reordered
  - The approval flow, ROADMAP move, and commit step are untouched

  Run: `make test-unit` — still PASS

---

## Task 2: Add context-load block to `commands/zie-implement.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-implement.md` contains a context-load block with marker `<!-- context-load: adrs + project context -->`
- The block loads `zie-framework/decisions/*.md` and `zie-framework/project/context.md`
- The impl-reviewer spawn (Step 6 of the task loop) passes `context_bundle`
- All other command logic (TDD loop, task tracker, final-wait, commit step) is unchanged

**Files:**
- Modify: `commands/zie-implement.md`
- Modify: `tests/unit/test_reviewer_shared_context.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_reviewer_shared_context.py — add after TestZiePlanContextLoad

  class TestZieImplementContextLoad:
      def test_context_load_marker_present(self):
          text = (COMMANDS_DIR / "zie-implement.md").read_text()
          assert "<!-- context-load: adrs + project context -->" in text, \
              "zie-implement.md must have context-load comment marker"

      def test_adrs_load_step_present(self):
          text = (COMMANDS_DIR / "zie-implement.md").read_text()
          assert "decisions/*.md" in text, \
              "zie-implement.md must load zie-framework/decisions/*.md"

      def test_context_md_load_step_present(self):
          text = (COMMANDS_DIR / "zie-implement.md").read_text()
          assert "project/context.md" in text, \
              "zie-implement.md must load zie-framework/project/context.md"

      def test_reviewer_invocation_passes_bundle(self):
          text = (COMMANDS_DIR / "zie-implement.md").read_text()
          assert "context_bundle" in text, \
              "zie-implement.md must pass context_bundle to reviewer invocation"
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-implement.md`, insert the following block immediately after the `### วิเคราะห์ dependency ระหว่าง tasks` section and before `## Steps`:

  ```markdown
  ## โหลด context bundle (ครั้งเดียวต่อ session)

  <!-- context-load: adrs + project context -->

  Before entering the task loop, load shared context once:

  1. Read all `zie-framework/decisions/*.md` → store as `adrs_content`
     (list of `{filename, content}` pairs; empty list if directory missing)
  2. Read `zie-framework/project/context.md` → store as `context_content`
     (string; empty string if file missing)
  3. Bundle as `context_bundle = { adrs: adrs_content, context: context_content }`

  Pass `context_bundle` to every impl-reviewer invocation in the task loop.
  ```

  Then in Step 6 of `## Steps`, update the impl-reviewer spawn line to:

  ```markdown
  - Invoke `@agent-impl-reviewer` (background: true):
    <!-- fallback: Skill(zie-framework:impl-reviewer) -->
    pass task description, **Acceptance Criteria** from plan task header,
    list of files changed in this task, and `context_bundle`.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read the full command file. Confirm:
  - Context-load block position does not interrupt the dependency-parse logic
  - Step 6 background-spawn behavior (handle capture, deferred-check loop, max 3 iterations) is intact
  - Final-wait block and commit step are untouched

  Run: `make test-unit` — still PASS

---

## Task 3: Add bundle fallback to `skills/spec-reviewer/SKILL.md`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `skills/spec-reviewer/SKILL.md` Phase 1 starts with a conditional preamble:
  if `context_bundle` provided by caller → use it; skip ADR + context.md disk reads
- If `context_bundle` absent → read from disk as today (existing Phase 1 steps 2 and 3 unchanged)
- Preamble contains the text `if context_bundle provided`
- All Phase 1 steps (named component files, ADRs, context, ROADMAP) are still listed
- Phase 2 and Phase 3 checklists are untouched

**Files:**
- Modify: `skills/spec-reviewer/SKILL.md`
- Modify: `tests/unit/test_reviewer_shared_context.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_reviewer_shared_context.py — add after TestZieImplementContextLoad

  class TestSpecReviewerFallback:
      def test_bundle_preamble_present(self):
          text = (SKILLS_DIR / "spec-reviewer" / "SKILL.md").read_text()
          assert "if context_bundle provided" in text, \
              "spec-reviewer SKILL.md Phase 1 must have bundle conditional preamble"

      def test_disk_fallback_mentioned(self):
          text = (SKILLS_DIR / "spec-reviewer" / "SKILL.md").read_text()
          assert "read from disk" in text, \
              "spec-reviewer SKILL.md must mention disk fallback path"

      def test_phase_1_steps_intact(self):
          text = (SKILLS_DIR / "spec-reviewer" / "SKILL.md").read_text()
          assert "decisions/*.md" in text, \
              "spec-reviewer SKILL.md Phase 1 must still reference decisions/*.md"
          assert "project/context.md" in text, \
              "spec-reviewer SKILL.md Phase 1 must still reference project/context.md"
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `skills/spec-reviewer/SKILL.md`, replace the opening of `## Phase 1 — Load Context Bundle` with:

  ```markdown
  ## Phase 1 — Load Context Bundle

  **If `context_bundle` provided by caller** — use it directly:
  - `adrs_content` ← `context_bundle.adrs` (skip step 2 below)
  - `context_content` ← `context_bundle.context` (skip step 3 below)

  **If `context_bundle` absent** — read from disk as fallback (backward-compatible):

  Before reviewing, load the following context (skip gracefully if missing —
  never block review):
  ```

  All four numbered steps (named component files, ADRs, context.md, ROADMAP) remain unchanged below this preamble.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read the full SKILL.md. Confirm:
  - The conditional preamble is before the four numbered steps, not inside them
  - Phase 2 and Phase 3 content is byte-for-byte identical to the pre-change state
  - Output format section is untouched

  Run: `make test-unit` — still PASS

---

## Task 4: Add bundle fallback to `skills/plan-reviewer/SKILL.md`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `skills/plan-reviewer/SKILL.md` Phase 1 contains `if context_bundle provided` preamble
- Disk fallback path still reads `decisions/*.md` and `project/context.md`
- Phase 2 and Phase 3 checklists are untouched

**Files:**
- Modify: `skills/plan-reviewer/SKILL.md`
- Modify: `tests/unit/test_reviewer_shared_context.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_reviewer_shared_context.py — add after TestSpecReviewerFallback

  class TestPlanReviewerFallback:
      def test_bundle_preamble_present(self):
          text = (SKILLS_DIR / "plan-reviewer" / "SKILL.md").read_text()
          assert "if context_bundle provided" in text, \
              "plan-reviewer SKILL.md Phase 1 must have bundle conditional preamble"

      def test_disk_fallback_mentioned(self):
          text = (SKILLS_DIR / "plan-reviewer" / "SKILL.md").read_text()
          assert "read from disk" in text, \
              "plan-reviewer SKILL.md must mention disk fallback path"

      def test_phase_1_steps_intact(self):
          text = (SKILLS_DIR / "plan-reviewer" / "SKILL.md").read_text()
          assert "decisions/*.md" in text, \
              "plan-reviewer SKILL.md Phase 1 must still reference decisions/*.md"
          assert "project/context.md" in text, \
              "plan-reviewer SKILL.md Phase 1 must still reference project/context.md"
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `skills/plan-reviewer/SKILL.md`, replace the opening of `## Phase 1 — Load Context Bundle` with the same conditional preamble used in Task 3:

  ```markdown
  ## Phase 1 — Load Context Bundle

  **If `context_bundle` provided by caller** — use it directly:
  - `adrs_content` ← `context_bundle.adrs` (skip step 2 below)
  - `context_content` ← `context_bundle.context` (skip step 3 below)

  **If `context_bundle` absent** — read from disk as fallback (backward-compatible):

  Before reviewing, load the following context (skip gracefully if missing —
  never block review):
  ```

  All four numbered steps (file map files, ADRs, context.md, ROADMAP) remain below this preamble unchanged.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read full SKILL.md. Confirm Phase 2 (9 checklist items) and Phase 3 (4 checks) are untouched. Confirm Output Format section is untouched.

  Run: `make test-unit` — still PASS

---

## Task 5: Add bundle fallback to `skills/impl-reviewer/SKILL.md`

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- `skills/impl-reviewer/SKILL.md` Phase 1 contains `if context_bundle provided` preamble
- Disk fallback path still reads `decisions/*.md` and `project/context.md`
- Modified-files read step (Phase 1 step 1) is unchanged — this is task-specific, never from bundle
- Phase 2 and Phase 3 checklists are untouched

**Files:**
- Modify: `skills/impl-reviewer/SKILL.md`
- Modify: `tests/unit/test_reviewer_shared_context.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_reviewer_shared_context.py — add after TestPlanReviewerFallback

  class TestImplReviewerFallback:
      def test_bundle_preamble_present(self):
          text = (SKILLS_DIR / "impl-reviewer" / "SKILL.md").read_text()
          assert "if context_bundle provided" in text, \
              "impl-reviewer SKILL.md Phase 1 must have bundle conditional preamble"

      def test_disk_fallback_mentioned(self):
          text = (SKILLS_DIR / "impl-reviewer" / "SKILL.md").read_text()
          assert "read from disk" in text, \
              "impl-reviewer SKILL.md must mention disk fallback path"

      def test_modified_files_step_intact(self):
          text = (SKILLS_DIR / "impl-reviewer" / "SKILL.md").read_text()
          assert "files changed" in text, \
              "impl-reviewer SKILL.md must still reference caller's files changed list"

      def test_phase_1_adr_ref_intact(self):
          text = (SKILLS_DIR / "impl-reviewer" / "SKILL.md").read_text()
          assert "decisions/*.md" in text, \
              "impl-reviewer SKILL.md Phase 1 must still reference decisions/*.md"
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `skills/impl-reviewer/SKILL.md`, replace the opening of `## Phase 1 — Load Context Bundle` with:

  ```markdown
  ## Phase 1 — Load Context Bundle

  **If `context_bundle` provided by caller** — use it for shared context:
  - `adrs_content` ← `context_bundle.adrs` (skip step 2 below)
  - `context_content` ← `context_bundle.context` (skip step 3 below)

  **If `context_bundle` absent** — read from disk as fallback (backward-compatible):

  Before reviewing, load the following context (skip gracefully if missing —
  never block review):
  ```

  Step 1 (modified files from caller's "files changed" input) remains the first numbered step as-is — it is task-specific and never provided via bundle.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read full SKILL.md. Confirm:
  - Step 1 (modified files) is still the first numbered item and unaltered
  - Steps 2 and 3 (ADRs, context.md) are still listed under the fallback path
  - Phase 2 (8 checklist items) and Phase 3 (3 checks) are untouched

  Run: `make test-unit` — still PASS

---

## Summary

| Task | File(s) | Depends on | Parallelizable |
| --- | --- | --- | --- |
| Task 1 | `commands/zie-plan.md` | none | yes (with Task 2) |
| Task 2 | `commands/zie-implement.md` | none | yes (with Task 1) |
| Task 3 | `skills/spec-reviewer/SKILL.md` | Task 1 | after Task 1 |
| Task 4 | `skills/plan-reviewer/SKILL.md` | Task 1 | after Task 1, parallel with Task 5 |
| Task 5 | `skills/impl-reviewer/SKILL.md` | Task 2 | after Task 2, parallel with Task 4 |

Tasks 1 and 2 are fully independent — run in parallel. Tasks 3, 4, 5 depend on their respective caller change landing first (so the fallback prose aligns with the exact `context_bundle` variable name established in the caller).

*Commit: `git add commands/zie-plan.md commands/zie-implement.md skills/spec-reviewer/SKILL.md skills/plan-reviewer/SKILL.md skills/impl-reviewer/SKILL.md tests/unit/test_reviewer_shared_context.py && git commit -m "feat: reviewer-shared-context"`*
