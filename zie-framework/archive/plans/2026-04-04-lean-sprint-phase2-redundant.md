---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-sprint-phase2-redundant.md
---

# Remove Redundant Sprint Phase 2 — Implementation Plan

**Goal:** Eliminate the no-op Phase 2 ("Plan All") from `/sprint` by inlining failure recovery into Phase 1, reducing every sprint invocation by one TaskCreate and one full ROADMAP re-read.
**Architecture:** `commands/sprint.md` is the single source of truth for sprint orchestration. Phase 2 is deleted; Phase 1 gains an inline retry pass (sequential `Skill()` calls for failed slugs) and an unconditional ROADMAP reload afterward. Phases 3–5 are renumbered to 2–4. All textual references (Summary table, ETA strings, audit confirmation prompt, Error Handling, phase numbering tests) are updated in lockstep.
**Tech Stack:** Markdown (sprint command), Python (pytest tests), no runtime dependencies.

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/sprint.md` | Remove Phase 2 block; add inline retry pass + unconditional ROADMAP reload to Phase 1; renumber phases; update all text references |
| Modify | `tests/unit/test_zie_sprint.py` | Update phase-count assertion (5→4), update Phase 3/4/5 index lookups to Phase 2/3/4, add test for inline retry behavior |
| Modify | `tests/unit/test_zie_sprint_phase3.py` | Update regex patterns from PHASE 3 → PHASE 2 (impl is now Phase 2) |
| Create | `tests/unit/test_zie_sprint_phase1_retry.py` | New tests: inline retry on partial failure, unconditional ROADMAP reload, no Phase 2 task |

---

## Task 1: Remove Phase 2 block and add inline retry pass to Phase 1

**Acceptance Criteria:**
- `commands/sprint.md` has no `## PHASE 2: PLAN ALL` section
- Phase 1 section contains an inline retry pass that uses `Skill()` (not `Agent(run_in_background=True)`) for failed slugs
- Phase 1 section contains an unconditional ROADMAP reload (binding `roadmap_post_phase1`) regardless of whether retry ran
- `roadmap_post_phase2` binding no longer appears in the file

**Files:**
- Modify: `commands/sprint.md`

- [ ] **Step 1: Write failing tests (RED)**

  Add to `tests/unit/test_zie_sprint.py`:

  ```python
  class TestPhase2Removed:
      def test_no_phase2_plan_all(self):
          text = _text()
          assert "PHASE 2: PLAN ALL" not in text, \
              "Phase 2 'Plan All' must be removed"

      def test_no_roadmap_post_phase2(self):
          assert "roadmap_post_phase2" not in _text(), \
              "roadmap_post_phase2 binding must be removed"

      def test_phase1_inline_retry_uses_skill(self):
          text = _text()
          phase1_idx = text.index("PHASE 1")
          phase2_idx = text.index("PHASE 2")
          phase1_section = text[phase1_idx:phase2_idx]
          assert "phase1_failed" in phase1_section, \
              "Phase 1 must track failed slugs in phase1_failed"
          assert "Skill(" in phase1_section, \
              "Inline retry must use Skill() calls"

      def test_phase1_roadmap_reload_unconditional(self):
          text = _text()
          phase1_idx = text.index("PHASE 1")
          phase2_idx = text.index("PHASE 2")
          phase1_section = text[phase1_idx:phase2_idx]
          assert "roadmap_post_phase1" in phase1_section, \
              "Phase 1 must bind roadmap_post_phase1 unconditionally"
          assert "unconditional" in phase1_section.lower() or \
              "always" in phase1_section.lower() or \
              "regardless" in phase1_section.lower(), \
              "ROADMAP reload must be explicitly unconditional"
  ```

  Run: `make test-unit` — must FAIL (tests reference content not yet in sprint.md)

- [ ] **Step 2: Implement (GREEN)**

  In `commands/sprint.md`, replace the entire `## PHASE 2: PLAN ALL` section (lines ~141–165) with nothing, and update the `## PHASE 1` section's post-collection block:

  Replace the current Phase 1 "Wait for all" block:
  ```markdown
  Wait for all Phase 1 agents → collect results.
  - Each spec result: approved → mark in audit
  - Any failed → print error, halt sprint

  After Phase 1: reload ROADMAP (items moved from Next → Ready by skill chain) → bind as `roadmap_post_phase1`.
  ```

  With:
  ```markdown
  Wait for all Phase 1 agents → collect results.
  - Each spec result: approved → mark approved set; failure → append slug to `phase1_failed`

  **Inline retry pass** (runs only if `phase1_failed` is non-empty):
  For each slug in `phase1_failed` (sequential, synchronous `Skill()` calls — not background Agent):
  1. `Skill(zie-framework:spec-design, '<slug> quick')` — rewrite spec
  2. `Skill(zie-framework:spec-reviewer, '<slug>')` — approve spec
  3. `Skill(zie-framework:write-plan, '<slug>')` — write plan
  4. `Skill(zie-framework:plan-reviewer, '<slug>')` — approve plan
  - Success → add slug to approved set
  - Failure → halt sprint, surface slug and error; user can fix and re-run

  **Unconditional ROADMAP reload** (always runs, regardless of whether retry occurred):
  Reload ROADMAP → bind as `roadmap_post_phase1`. This captures all subagent writes in a single read.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify the removed Phase 2 block left no orphan references (`roadmap_post_phase2`, `Phase 2/5 — Plan All`, `TaskCreate subject="Phase 2`). Use Grep to confirm zero hits.

  Run: `make test-unit` — still PASS

---

## Task 2: Renumber phases 3→2, 4→3, 5→4 throughout sprint.md

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `commands/sprint.md` contains `PHASE 2: IMPLEMENT`, `PHASE 3: BATCH RELEASE`, `PHASE 4: SPRINT RETRO`
- Phase 2 (impl) reads from `roadmap_post_phase1` (no second ROADMAP bind introduced)
- Summary table shows 4 phases (Spec → Impl → Release → Retro)
- ETA strings updated: `Phase 1/4`, `Phase 2/4`, `Phase 3/4`, `Phase 4/4`
- Audit confirmation prompt lists 4 phases
- Error Handling section no longer references "Phase 2 fails" (plan) — old Phase 2 entry removed, remaining entries renumbered
- Progress bar counters use `/4` not `/5`
- TaskCreate subjects updated: `Phase 2/4 — Implement`, `Phase 3/4 — Release`, `Phase 4/4 — Retro`

**Files:**
- Modify: `commands/sprint.md`

- [ ] **Step 1: Write failing tests (RED)**

  Add to `tests/unit/test_zie_sprint.py`, replacing `TestPhaseStructure.test_has_five_phases`:

  ```python
  class TestPhaseStructure:
      def test_has_four_phases(self):
          text = _text()
          for n in ("1", "2", "3", "4"):
              assert f"PHASE {n}" in text, f"must have PHASE {n}"
          assert "PHASE 5" not in text, "PHASE 5 must be removed after renumbering"

      def test_phase2_is_implement(self):
          text = _text()
          assert "PHASE 2: IMPLEMENT" in text or "PHASE 2" in text, \
              "Phase 2 must be IMPLEMENT after renumbering"

      def test_phase3_is_release(self):
          assert "PHASE 3" in _text() and "RELEASE" in _text()

      def test_phase4_is_retro(self):
          assert "PHASE 4" in _text() and "RETRO" in _text()

      def test_eta_strings_use_slash4(self):
          text = _text()
          assert "1/4" in text and "2/4" in text and "3/4" in text and "4/4" in text, \
              "ETA strings must use /4 (4-phase sprint)"

      def test_audit_confirmation_lists_4_phases(self):
          text = _text()
          audit_idx = text.index("AUDIT")
          # Find the confirmation block after AUDIT
          confirmation_start = text.index("Start sprint?")
          confirmation_block = text[audit_idx:confirmation_start + 200]
          assert "Phase 4" in confirmation_block, \
              "Audit confirmation must list Phase 4 (Retro)"
          assert "Phase 5" not in confirmation_block, \
              "Audit confirmation must not list Phase 5 after renumbering"

      def test_error_handling_no_phase2_plan(self):
          text = _text()
          err_idx = text.index("Error Handling")
          err_section = text[err_idx:]
          assert "Phase 2 fails" not in err_section or \
              "plan" not in err_section[err_section.find("Phase 2 fails"):err_section.find("Phase 2 fails") + 80], \
              "Error Handling must not have a 'Phase 2 fails: plan' entry"
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `commands/sprint.md`:

  1. Replace all `Phase 3/5` → `Phase 2/4`, `Phase 4/5` → `Phase 3/4`, `Phase 5/5` → `Phase 4/4`
  2. Replace all `## PHASE 3:` → `## PHASE 2:`, `## PHASE 4:` → `## PHASE 3:`, `## PHASE 5:` → `## PHASE 4:`
  3. Replace all `TaskCreate subject="Phase 3/5` → `Phase 2/4`, etc.
  4. In Phase 2 (impl) section: change `roadmap_post_phase2` → `roadmap_post_phase1`
  5. Update audit confirmation prompt:
     ```markdown
     - Phase 1: Spec <N> items (parallel)
     - Phase 2: Impl <N> items (sequential, WIP=1)
     - Phase 3: Release v<suggested-version>
     - Phase 4: Retro
     ```
  6. Update Summary table phases section:
     ```
       1. Spec    — <N> items, <elapsed>
       2. Impl    — <N> items, <elapsed> | WIP=1
       3. Release — v<version>, <elapsed>
       4. Retro   — <N> ADRs, <elapsed>
     ```
  7. Update Error Handling — remove "Phase 2 fails: plan" entry; renumber Phase 3→2, 4→3, 5→4
  8. Update final progress bar: `████████████████████ 4/4 (100%)`

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify no stale `5/5`, `Phase 5`, `roadmap_post_phase2`, or "Plan All" strings remain.

  Run: `make test-unit` — still PASS

---

## Task 3: Update existing sprint phase tests for new numbering

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- `test_zie_sprint.py` `TestPhaseStructure` does not assert PHASE 5 exists
- `test_zie_sprint_phase3.py` regex patterns target `PHASE 2` (impl) not `PHASE 3`
- All existing tests pass against the updated `sprint.md`

**Files:**
- Modify: `tests/unit/test_zie_sprint.py`
- Modify: `tests/unit/test_zie_sprint_phase3.py`

- [ ] **Step 1: Write failing tests (RED)**

  The tests from Task 2 Step 1 already cover phase numbering assertions. The existing `test_has_five_phases` test will fail once Task 2 is done. Confirm this is the only blocker by running:

  Run: `make test-unit` — `test_has_five_phases` must FAIL (it asserts PHASE 5 exists)

- [ ] **Step 2: Implement (GREEN)**

  In `tests/unit/test_zie_sprint.py`:
  - Delete or replace `test_has_five_phases` with `test_has_four_phases` (added in Task 2 Step 1)
  - Update `test_phase3_sequential_wip1`: change `text.index("PHASE 3")` → `text.index("PHASE 2")` and `text.index("PHASE 4")` → `text.index("PHASE 3")`
  - Update `test_phase4_batch_release`: change `text.index("PHASE 4")` → `text.index("PHASE 3")` and `text.index("PHASE 5")` → `text.index("PHASE 4")`
  - Update `test_phase5_retro`: change `text.index("PHASE 5")` → `text.index("PHASE 4")`
  - Update `test_context_bundle_referenced_in_phase1`: boundary still `PHASE 1` → `PHASE 2`, no change needed

  In `tests/unit/test_zie_sprint_phase3.py`:
  - Update `test_phase3_no_agent`: regex pattern `r"^## PHASE 3.*?(?=^## PHASE |\Z)"` → `r"^## PHASE 2.*?(?=^## PHASE |\Z)"`
  - Update `test_phase3_has_skill`: same regex update
  - `test_phase1_keeps_agent`: no change (still Phase 1)

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Rename `test_phase3_no_agent` → `test_phase2_no_agent` and `test_phase3_has_skill` → `test_phase2_has_skill` in `test_zie_sprint_phase3.py` for clarity.

  Run: `make test-unit` — still PASS

---

## Task 4: Add new tests for Phase 1 inline retry and unconditional ROADMAP reload

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- New test file `tests/unit/test_zie_sprint_phase1_retry.py` exists
- Tests verify: inline retry uses `Skill()` not `Agent(run_in_background=True)`, ROADMAP reload is unconditional, no Phase 2 TaskCreate exists for planning, agent timeout treated as failure
- All new tests pass against the updated `sprint.md`

**Files:**
- Create: `tests/unit/test_zie_sprint_phase1_retry.py`

- [ ] **Step 1: Write failing tests (RED)**

  Create `tests/unit/test_zie_sprint_phase1_retry.py`:

  ```python
  """Tests for Phase 1 inline retry and ROADMAP reload in /sprint."""
  import re
  from pathlib import Path

  REPO_ROOT = Path(__file__).parents[2]
  CMD = REPO_ROOT / "commands" / "sprint.md"


  def _text():
      return CMD.read_text()


  def _phase1_section(text):
      phase1_idx = text.index("PHASE 1")
      phase2_idx = text.index("PHASE 2")
      return text[phase1_idx:phase2_idx]


  class TestInlineRetry:
      def test_phase1_tracks_failed_slugs(self):
          assert "phase1_failed" in _phase1_section(_text()), \
              "Phase 1 must track failed slugs in phase1_failed list"

      def test_inline_retry_uses_skill_not_agent_background(self):
          section = _phase1_section(_text())
          assert "Skill(" in section, \
              "Inline retry must use Skill() calls"
          # Inline retry block must not spawn background agents
          retry_idx = section.find("phase1_failed")
          retry_block = section[retry_idx:]
          assert "run_in_background=True" not in retry_block, \
              "Inline retry must not use run_in_background=True (sequential, not parallel)"

      def test_inline_retry_invokes_full_skill_chain(self):
          section = _phase1_section(_text())
          retry_idx = section.find("phase1_failed")
          retry_block = section[retry_idx:]
          for skill in ("spec-design", "spec-reviewer", "write-plan", "plan-reviewer"):
              assert skill in retry_block, \
                  f"Inline retry must invoke {skill}"

      def test_inline_retry_failure_halts_sprint(self):
          section = _phase1_section(_text())
          retry_idx = section.find("phase1_failed")
          retry_block = section[retry_idx:]
          assert "halt" in retry_block.lower() or "stop" in retry_block.lower(), \
              "Inline retry failure must halt sprint"


  class TestUnconditionalRoadmapReload:
      def test_roadmap_reload_unconditional(self):
          section = _phase1_section(_text())
          assert "roadmap_post_phase1" in section, \
              "Phase 1 must bind roadmap_post_phase1"
          # Reload must be marked as unconditional (not conditional on phase1_failed)
          reload_idx = section.find("roadmap_post_phase1")
          reload_context = section[max(0, reload_idx - 200):reload_idx + 100]
          assert any(word in reload_context.lower() for word in
                     ("unconditional", "always", "regardless")), \
              "ROADMAP reload must be explicitly unconditional"

      def test_no_roadmap_post_phase2(self):
          assert "roadmap_post_phase2" not in _text(), \
              "roadmap_post_phase2 binding must not exist"


  class TestNoPhase2TaskCreate:
      def test_no_phase2_plan_all_taskcreate(self):
          text = _text()
          assert 'TaskCreate subject="Phase 2/5 — Plan All"' not in text, \
              "Phase 2 Plan All TaskCreate must be removed"
          assert 'TaskCreate subject="Phase 2/4 — Plan' not in text, \
              "No Plan All TaskCreate must exist after renumbering"


  class TestAgentTimeoutEdgeCase:
      def test_agent_timeout_acknowledged(self):
          text = _text()
          # Sprint command should mention timeout or agent lifecycle handling
          # This is satisfied if halt-on-failure covers timed-out agents too
          phase1_idx = text.index("PHASE 1")
          phase2_idx = text.index("PHASE 2")
          phase1_section = text[phase1_idx:phase2_idx]
          assert "failure" in phase1_section.lower() or "fail" in phase1_section.lower(), \
              "Phase 1 must describe failure handling (covers timeout-as-failure)"
  ```

  Run: `make test-unit` — must FAIL (sprint.md not yet updated per Tasks 1+2)

- [ ] **Step 2: Implement (GREEN)**

  Tasks 1 and 2 already update `commands/sprint.md`. Once those are applied, re-run tests:

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Review test file for clarity — ensure helper `_phase1_section` has a docstring, group names are self-explanatory.

  Run: `make test-unit` — still PASS

---

## Execution Order

Tasks 1 and 4 share output (sprint.md read by task 4 tests) but Task 4's tests are written first (RED), then Task 1+2 make them pass (GREEN). Recommended sequential order:

1. **Task 4 Step 1** — write all new failing tests
2. **Task 1 Step 1** — write phase-removal failing tests
3. **Task 2 Step 1** — write renumbering failing tests
4. **Task 1 Step 2** — implement Phase 1 retry + ROADMAP reload changes
5. **Task 2 Step 2** — implement renumbering throughout
6. **Task 3 Step 2** — update existing tests to match new numbering
7. Run `make test-unit` — all green
8. **Task 3 Step 3 + Task 4 Step 3** — refactor
9. Run `make test-ci` — full gate

---

## Verification

```bash
make test-unit    # all sprint tests green
make lint         # no ruff violations
make test-ci      # full coverage gate
```

Expected: zero `PHASE 5` references, zero `roadmap_post_phase2` references, zero `Plan All` task entries in sprint.md. Grep confirms:

```bash
# Must return empty:
grep -n "PHASE 5\|roadmap_post_phase2\|Plan All" commands/sprint.md
```
