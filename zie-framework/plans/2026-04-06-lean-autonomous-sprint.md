---
approved: true
approved_at: 2026-04-06
backlog:
---

# Lean Autonomous Sprint — Implementation Plan

**Goal:** Make `/sprint` run unattended from backlog audit to retro, cutting token usage ~55–65% by replacing agent spawns with inline operations and eliminating user gates.

**Architecture:** Five targeted edits across commands and skills. `sprint.md` gains an `autonomous_mode` context flag and calls spec/plan skills directly (no intermediate Agent). `spec-design` and `write-plan` gain an `autonomous` mode that skips interactive steps. `implement.md` replaces background impl-reviewer Agent with inline check + auto-fix. `retro.md` gains a light mode gated by a plan tag.

**Tech Stack:** Markdown command/skill files · Python pytest unit tests (structural assertions on file content)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/spec-design/SKILL.md` | Add `autonomous` mode: skip Q&A+review, auto-approve |
| Modify | `skills/write-plan/SKILL.md` | Add `--autonomous` flag: inline plan-reviewer, auto-approve |
| Modify | `commands/implement.md` | Replace `@agent-impl-reviewer` with inline review + auto-fix |
| Modify | `commands/retro.md` | Add light mode: ROADMAP+summary only; full ADR gated on tag |
| Modify | `commands/sprint.md` | Autonomous mode: clarity detection, direct Skill calls, auto-retro |
| Create | `tests/unit/test_spec_design_autonomous_mode.py` | Verify autonomous_mode section |
| Create | `tests/unit/test_write_plan_autonomous_mode.py` | Verify --autonomous flag + inline reviewer |
| Create | `tests/unit/test_impl_reviewer_inline.py` | Verify inline review replaces agent spawn |
| Modify | `tests/unit/test_impl_reviewer_risk_based.py` | Update TestReviewerGate for inline reviewer |
| Create | `tests/unit/test_retro_light_mode.py` | Verify light mode + adr: required gate |
| Create | `tests/unit/test_sprint_autonomous_mode.py` | Verify autonomous_mode + clarity detection + auto-retro |

---

### Task 1: spec-design — autonomous mode

**Acceptance Criteria:**
- `spec-design` skill documents an `autonomous` mode for `$ARGUMENTS[1]`
- In autonomous mode: skip clarifying questions, approaches, and user review loop
- spec-reviewer runs inline; result auto-approves with no user gate
- Standalone `/spec` behavior unchanged (defaults to `full` mode)

**Files:**
- Modify: `skills/spec-design/SKILL.md`
- Create: `tests/unit/test_spec_design_autonomous_mode.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_spec_design_autonomous_mode.py
  from pathlib import Path

  SKILL = Path(__file__).parents[2] / "skills" / "spec-design" / "SKILL.md"


  def text():
      return SKILL.read_text()


  class TestSpecDesignAutonomousMode:
      def test_autonomous_mode_argument_documented(self):
          assert "autonomous" in text(), \
              "spec-design must document autonomous as a valid $ARGUMENTS[1] value"

      def test_skips_interactive_steps_in_autonomous(self):
          t = text().lower()
          assert "autonomous" in t and ("skip" in t or "direct" in t), \
              "autonomous mode must skip interactive steps"

      def test_auto_approve_in_autonomous(self):
          t = text().lower()
          assert "autonomous" in t and ("auto-approve" in t or "automatically" in t), \
              "autonomous mode must auto-approve without user gate"

      def test_inline_reviewer_call_in_autonomous(self):
          t = text().lower()
          assert "autonomous" in t and "inline" in t, \
              "autonomous mode must call spec-reviewer inline"

      def test_standalone_mode_unchanged(self):
          assert "full" in text() and "quick" in text(), \
              "full and quick modes must remain documented (standalone /spec unchanged)"
  ```

  Run: `make test-unit` — must FAIL (autonomous not yet in spec-design)

- [ ] **Step 2: Implement (GREEN)**

  In `skills/spec-design/SKILL.md`, update the Arguments table to add `autonomous` as a valid value for `$ARGUMENTS[1]`, then insert an **Autonomous Mode** section after the Completeness Check section:

  ```markdown
  ## Autonomous Mode

  When `$ARGUMENTS[1]` is `autonomous`:

  - Skip Steps 1, 2, 3 (clarifying questions, approaches proposal, user review loop)
  - Write spec directly from backlog content (Step 4) — treat all sections as accepted
  - Run spec-reviewer inline (Skill call in same context — no Agent spawn)
  - ✅ APPROVED → write `approved: true` frontmatter automatically (Step 6). No user gate.
  - ❌ Issues Found → fix inline (1 pass) → re-check once → auto-approve on pass
  - On second failure → surface to user (Interruption Protocol case 2)

  **Used by:** `/sprint` autonomous execution.
  **Not for:** standalone `/spec` — that always uses `full` or `quick`.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Ensure the new section sits cleanly after the Completeness Check section and before the Steps section. No prose duplication.
  Run: `make test-unit` — still PASS

---

### Task 2: write-plan — autonomous mode

**Acceptance Criteria:**
- `write-plan` skill documents a `--autonomous` flag in `$ARGUMENTS[1]`
- In autonomous mode: plan-reviewer runs inline, plan auto-approves on pass
- Standalone `/plan` behavior unchanged

**Files:**
- Modify: `skills/write-plan/SKILL.md`
- Create: `tests/unit/test_write_plan_autonomous_mode.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_write_plan_autonomous_mode.py
  from pathlib import Path

  SKILL = Path(__file__).parents[2] / "skills" / "write-plan" / "SKILL.md"


  def text():
      return SKILL.read_text()


  class TestWritePlanAutonomousMode:
      def test_autonomous_flag_documented(self):
          assert "--autonomous" in text(), \
              "write-plan must document --autonomous flag"

      def test_inline_plan_reviewer_in_autonomous(self):
          t = text().lower()
          assert "--autonomous" in text() and "inline" in t, \
              "autonomous mode must run plan-reviewer inline"

      def test_auto_approve_in_autonomous(self):
          t = text().lower()
          assert "--autonomous" in text() and ("auto-approve" in t or "automatically" in t), \
              "autonomous mode must auto-approve plan without user gate"

      def test_standalone_behavior_documented(self):
          assert "--no-memory" in text(), \
              "existing --no-memory flag must remain (standalone behavior unchanged)"
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `skills/write-plan/SKILL.md`, add `--autonomous` to the flags description in the Arguments table, then insert an **Autonomous Mode** section after the Notes section:

  ```markdown
  ## Autonomous Mode

  When `$ARGUMENTS[1]` contains `--autonomous`:

  - Write plan as normal (all task sections, file map, TDD steps)
  - Run `plan-reviewer` inline (Skill call in same context — no Agent spawn)
  - ✅ APPROVED → write `approved: true` frontmatter, move ROADMAP Next → Ready automatically
  - ❌ Issues Found → fix inline (1 pass) → re-check once → auto-approve on pass
  - On second failure → surface to user

  **Used by:** `/sprint` autonomous execution.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  No cleanup needed beyond verifying the section is well-placed.
  Run: `make test-unit` — still PASS

---

### Task 3: implement.md — inline impl-reviewer

**Acceptance Criteria:**
- Background `@agent-impl-reviewer` Agent spawn is removed
- Inline review replaces it for HIGH-risk tasks
- Auto-fix protocol: issues → fix → `make test-unit` → pass → continue; fail → interrupt
- Risk classification (HIGH/LOW) and LOW-skip path unchanged
- Test `test_reviewer_gated_on_high` updated to check for inline review

**Files:**
- Modify: `commands/implement.md`
- Modify: `tests/unit/test_impl_reviewer_risk_based.py`
- Create: `tests/unit/test_impl_reviewer_inline.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_impl_reviewer_inline.py
  from pathlib import Path

  CMD = Path(__file__).parents[2] / "commands" / "implement.md"


  def text():
      return CMD.read_text()


  class TestInlineImplReviewer:
      def test_inline_review_present(self):
          assert "inline review" in text().lower() or "inline impl-review" in text().lower(), \
              "implement.md must describe inline review for HIGH-risk tasks"

      def test_no_background_agent_spawn(self):
          assert "@agent-impl-reviewer" not in text(), \
              "implement.md must not spawn @agent-impl-reviewer background agent"

      def test_auto_fix_protocol_present(self):
          t = text().lower()
          assert "auto-fix" in t or ("fix" in t and "retry" in t), \
              "implement.md must describe auto-fix protocol after review issues"

      def test_interrupt_on_fix_failure(self):
          t = text().lower()
          assert "interrupt" in t or "surface" in t, \
              "implement.md must interrupt sprint when auto-fix fails"
  ```

  Run: `make test-unit` — must FAIL (`@agent-impl-reviewer` still present, `inline review` absent)

- [ ] **Step 2: Implement (GREEN)**

  In `commands/implement.md`, find step 4 in the Task Loop (the `@agent-impl-reviewer` spawn block) and replace it:

  **Remove:**
  ```
  4. **Spawn async impl-reviewer** (HIGH only): `@agent-impl-reviewer` (background) with task description, AC, changed files, `context_bundle`. Record in pending list. Do NOT block.
     - At each loop start: poll `reviewer_status` → `approved` clear; `issues_found` halt, fix, re-run `make test-unit`, re-invoke. Max 2 total iterations; confirm pass required. If 0 issues → APPROVED immediately.
  5. **→ LOW risk:** `make test-unit` + `[risk: LOW] Skipping impl-reviewer`.
  ```

  **Replace with:**
  ```
  4. **Inline impl-review** (HIGH only): Check changed files in current context — no Agent spawn.
     - Review changed files against task AC, project patterns, and security (ADR cross-check if context_bundle available)
     - ✅ No issues → continue
     - ❌ Issues found → auto-fix inline → `make test-unit`
       - Pass → continue
       - Fail after 1 retry → surface issue + interrupt (Interruption Protocol case 2)
  5. **→ LOW risk:** `make test-unit` + `[risk: LOW] Skipping impl-reviewer`.
  ```

  Then update `tests/unit/test_impl_reviewer_risk_based.py` — find `test_reviewer_gated_on_high` and update the assertion:

  **Remove:**
  ```python
  def test_reviewer_gated_on_high(self):
      t = text()
      assert "risk_level" in t and "HIGH" in t and "@agent-impl-reviewer" in t, \
          "Reviewer invocation must be present and gated by risk_level"
  ```

  **Replace with:**
  ```python
  def test_reviewer_gated_on_high(self):
      t = text()
      assert "risk_level" in t and "HIGH" in t, \
          "Reviewer invocation must be gated by risk_level=HIGH"

  def test_inline_review_gated_on_high(self):
      t = text().lower()
      assert "inline" in t and "high" in t, \
          "Inline review must be present and gated on HIGH risk"
  ```

  Also update `test_reviewer_not_invoked_unconditionally` — remove the `@agent-impl-reviewer` reference:

  **Remove:**
  ```python
  def test_reviewer_not_invoked_unconditionally(self):
      t = text()
      lines = t.splitlines()
      reviewer_lines = [i for i, ln in enumerate(lines) if "@agent-impl-reviewer" in ln]
      assert reviewer_lines, "Reviewer invocation line must exist"
      for idx in reviewer_lines:
          context_block = "\n".join(lines[max(0, idx - 10):idx + 1])
          assert "HIGH" in context_block, \
              f"@agent-impl-reviewer at line {idx+1} must be inside a HIGH risk guard"
  ```

  **Replace with:**
  ```python
  def test_reviewer_not_invoked_unconditionally(self):
      t = text().lower()
      # Inline review must appear inside HIGH risk guard block, not unconditionally
      lines = t.splitlines()
      inline_lines = [i for i, ln in enumerate(lines) if "inline" in ln and "review" in ln]
      assert inline_lines, "Inline review line must exist in implement.md"
      for idx in inline_lines:
          context_block = "\n".join(lines[max(0, idx - 10):idx + 1])
          assert "high" in context_block, \
              f"Inline review at line {idx+1} must be inside a HIGH risk guard"
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify the "When All Tasks Complete" section no longer references reviewer polling (`poll reviewer_status`, `pending reviewers`). Remove those lines if present.
  Run: `make test-unit` — still PASS

---

### Task 4: retro.md — light mode

**Acceptance Criteria:**
- Light mode: ROADMAP Done update + ADR-000-summary.md update always run
- Full ADR written only when any shipped plan contains `<!-- adr: required -->`
- All existing retro behavior (inline ADR format, auto-commit, non-blocking push) preserved

**Files:**
- Modify: `commands/retro.md`
- Create: `tests/unit/test_retro_light_mode.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_retro_light_mode.py
  from pathlib import Path

  CMD = Path(__file__).parents[2] / "commands" / "retro.md"


  def text():
      return CMD.read_text()


  class TestRetroLightMode:
      def test_adr_required_tag_gate(self):
          assert "adr: required" in text(), \
              "retro.md must gate full ADR on <!-- adr: required --> tag in plan"

      def test_roadmap_update_always_runs(self):
          t = text()
          assert "ROADMAP" in t and "Done" in t, \
              "ROADMAP Done update must always run (not gated)"

      def test_adr_summary_always_runs(self):
          assert "ADR-000-summary" in text(), \
              "ADR-000-summary.md update must always run (not gated)"

      def test_full_adr_gated_description(self):
          t = text().lower()
          assert "adr: required" in text() and ("skip" in t or "only" in t or "gated" in t), \
              "retro must describe skipping full ADR when tag absent"
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `commands/retro.md`, find the ADR writing section (where it creates ADR files) and wrap it in a conditional:

  Add before the ADR writing step:

  ```markdown
  **ADR gate (light mode check):**
  Scan all plan files shipped in this release (`zie-framework/plans/` — files matching shipped slugs):
  - If any plan contains `<!-- adr: required -->` → write full ADR(s) as normal (continue to ADR steps below)
  - If no plan has this tag → skip full ADR writing. Update `decisions/ADR-000-summary.md` only (append one-line entry for this release). Continue to commit step.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify the gate check is placed logically — after context gathering, before the ADR number count step.
  Run: `make test-unit` — still PASS

---

### Task 5: sprint.md — autonomous orchestration

<!-- depends_on: Task 1, Task 2, Task 3, Task 4 -->

**Acceptance Criteria:**
- Sprint sets `autonomous_mode=true` before Phase 1
- Step 0 AUDIT includes clarity scoring per backlog item (score ≥ 2 = direct-write, < 2 = ask 1 question)
- Phase 1 calls `Skill(spec-design, '<slug> autonomous')` and `Skill(write-plan, '<slug> --autonomous')` directly — no intermediate Agent spawn
- Phase 4 auto-runs retro (no user prompt). Retro runs in light mode by default.
- All existing sprint test assertions still pass (parallel, retry, skill chain, phase structure)

**Files:**
- Modify: `commands/sprint.md`
- Create: `tests/unit/test_sprint_autonomous_mode.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_sprint_autonomous_mode.py
  from pathlib import Path

  CMD = Path(__file__).parents[2] / "commands" / "sprint.md"


  def text():
      return CMD.read_text()


  class TestSprintAutonomousMode:
      def test_autonomous_mode_context_variable(self):
          assert "autonomous_mode" in text(), \
              "sprint.md must set autonomous_mode context variable"

      def test_clarity_detection_present(self):
          t = text().lower()
          assert "clarity" in t or ("score" in t and "problem" in t), \
              "sprint.md must include backlog clarity detection logic"

      def test_phase1_calls_autonomous_spec_design(self):
          t = text()
          phase1_idx = t.index("PHASE 1")
          phase2_idx = t.index("PHASE 2")
          phase1 = t[phase1_idx:phase2_idx]
          assert "autonomous" in phase1.lower(), \
              "Phase 1 must call spec-design with autonomous mode"

      def test_phase1_no_intermediate_agent_spawn(self):
          t = text()
          phase1_idx = t.index("PHASE 1")
          phase2_idx = t.index("PHASE 2")
          phase1 = t[phase1_idx:phase2_idx]
          # The general-purpose intermediary agent must be gone
          assert 'subagent_type="general-purpose"' not in phase1 and \
                 "subagent_type='general-purpose'" not in phase1, \
              "Phase 1 must not spawn general-purpose agent intermediary"

      def test_phase4_auto_retro(self):
          t = text()
          phase4_idx = t.index("PHASE 4")
          phase4 = t[phase4_idx:]
          assert "auto" in phase4.lower() or "automatically" in phase4.lower(), \
              "Phase 4 must auto-run retro without user prompt"

      def test_interruption_protocol_documented(self):
          t = text().lower()
          assert "interrupt" in t or "interruption" in t, \
              "sprint.md must document when to interrupt user"
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  **2a. Add clarity scoring to Step 0 AUDIT** — after the classify items block, add:

  ```markdown
  **Clarity scoring** (per Next item needing spec):
  For each slug in `needs_spec`:
  - +1 if `## Problem` has ≥ 2 sentences
  - +1 if `## Rough Scope` has content
  - +1 if title names a concrete action ("add X", "fix Y", "remove Z")
  - Score ≥ 2 → `[clarity: direct]` (write spec without Q&A)
  - Score < 2 → `[clarity: ask]` (ask 1 clarifying question, then write)
  ```

  **2b. Add autonomous_mode before Phase 1:**

  After the Load Context Bundle section, insert:

  ```markdown
  ## Autonomous Mode

  Set `autonomous_mode=true` for all downstream skill invocations.
  This flag suppresses interactive turns, approval gates, and agent spawns in spec-design, write-plan, and retro.
  **Interruption Protocol** — sprint pauses for user only in 3 cases:
  1. Backlog clarity score < 2 → ask 1 question per vague item
  2. Auto-fix failed after 1 retry → surface issue + ask
  3. Unresolvable dependency conflict between items → ask once before Phase 1
  ```

  **2c. Replace Phase 1 Agent spawn with direct Skill calls:**

  Replace the current Phase 1 agent-spawn block:
  ```
  Spawn Agent(subagent_type="general-purpose", run_in_background=True):
      prompt: "Run spec + plan workflow for slug: <slug>. ..."
  ```

  With:
  ```markdown
  For each item in needs_spec, launch in parallel (multiple Skill calls simultaneously):
    `Skill(zie-framework:spec-design, '<slug> autonomous')` — writes spec, runs spec-reviewer inline, auto-approves
    After spec approved: `Skill(zie-framework:write-plan, '<slug> --autonomous')` — writes plan, runs plan-reviewer inline, auto-approves

  For clarity=ask items: ask the 1 question first, then launch the Skill call.
  ```

  **2d. Phase 4 auto-retro** — replace the current Phase 4 block that prompts for retro:

  ```markdown
  ## PHASE 4: SPRINT RETRO (auto)

  Auto-invoke retro inline — no user prompt. Retro runs in light mode (ROADMAP Done + ADR-000-summary only).
  Full ADR writing triggered only if any shipped plan contains `<!-- adr: required -->`.

  Invoke `/retro` with sprint context.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify existing sprint tests still pass:
  - `test_phase1_spec_parallel` — parallel Skill calls satisfy "parallel" assertion ✓
  - `test_phase1_uses_skill_chain` — spec-reviewer, write-plan, plan-reviewer still referenced ✓
  - `test_phase1_has_inline_retry` — retry logic still documented ✓
  - All other phase/structure tests ✓

  Run: `make test-unit` — still PASS. Also run `make test-ci` for full suite.
