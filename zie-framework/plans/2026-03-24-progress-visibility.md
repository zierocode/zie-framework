---
approved: false
approved_at: ~
backlog: backlog/progress-visibility.md
spec: specs/2026-03-24-progress-visibility-design.md
---

# Progress Visibility for Long-Running Commands — Implementation Plan

**Goal:** Add consistent progress announcements (phase/step counters) to all six
long-running commands. Output-only additions — no behavioral changes.
**Architecture:** Each command file receives inline counter strings at phase/step
boundaries. Tests assert specific counter strings are present in each file using
`Path.read_text()`.
**Tech Stack:** Markdown (command definitions), pytest (string presence checks)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-implement.md` | Add `[T1/N]` task counters + phase markers + checkpoint line |
| Modify | `commands/zie-audit.md` | Add `[Phase 1/5]` phase counters + agent/search counters |
| Modify | `commands/zie-release.md` | Add `[Gate N/7]` gate counters + `[Step N/12]` post-gate steps |
| Modify | `commands/zie-plan.md` | Add `[Plan N/M]` per-slug counters + reviewer pass markers |
| Modify | `commands/zie-resync.md` | Add "Exploring codebase..." start marker + completion summary |
| Modify | `commands/zie-retro.md` | Add `[ADR N/M]` per-ADR counters + phase markers |
| Create | `tests/unit/test_progress_visibility.py` | Assert counter strings present in each command file |

---

## Task 1: Add progress counters to `commands/zie-implement.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-implement.md` contains the string `[T1/N]` (or equivalent pattern `[T` followed by task counter notation)
- Contains `→ RED` phase marker text
- Contains `→ GREEN` phase marker text
- Contains `→ REFACTOR` phase marker text
- Contains `done — ` checkpoint completion text
- Contains `checkpoint` or `Checkpoint` summary text

**Counter strings to add:**
- Task announce line: `"[T{N}/{total}] {task_description}"`  — replace step 1 "Announce task" instruction to emit this format
- Phase markers inline within the TDD loop steps:
  - RED step: emit `→ RED` before writing test
  - GREEN step: emit `→ GREEN` before writing implementation
  - REFACTOR step: emit `→ REFACTOR` before refactoring
- Task end: emit `✓ done — {remaining} remaining`
- Checkpoint (every 3 tasks or at halfway): emit `Checkpoint [{N}/{total}]: {completed_list} | remaining: {remaining_list}`

**Files:**
- Modify: `commands/zie-implement.md`
- Create: `tests/unit/test_progress_visibility.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_progress_visibility.py
  from pathlib import Path

  COMMANDS_DIR = Path(__file__).parents[2] / "commands"


  class TestImplementProgress:
      def test_task_counter_marker_present(self):
          text = (COMMANDS_DIR / "zie-implement.md").read_text()
          assert "[T" in text and "/N]" in text or "[T{N}" in text or "[T{n}" in text.lower(), \
              "zie-implement.md must contain task counter notation [TN/total]"

      def test_red_phase_marker_present(self):
          text = (COMMANDS_DIR / "zie-implement.md").read_text()
          assert "→ RED" in text, "zie-implement.md must contain → RED phase marker"

      def test_green_phase_marker_present(self):
          text = (COMMANDS_DIR / "zie-implement.md").read_text()
          assert "→ GREEN" in text, "zie-implement.md must contain → GREEN phase marker"

      def test_refactor_phase_marker_present(self):
          text = (COMMANDS_DIR / "zie-implement.md").read_text()
          assert "→ REFACTOR" in text, "zie-implement.md must contain → REFACTOR phase marker"

      def test_task_done_marker_present(self):
          text = (COMMANDS_DIR / "zie-implement.md").read_text()
          assert "done —" in text, "zie-implement.md must contain 'done —' completion marker"

      def test_checkpoint_marker_present(self):
          text = (COMMANDS_DIR / "zie-implement.md").read_text()
          assert "heckpoint" in text, "zie-implement.md must contain checkpoint summary marker"
  ```
  Run: `make test-unit` — must FAIL (markers not yet present)

- [ ] **Step 2: Implement (GREEN)**
  In `commands/zie-implement.md`, apply these targeted edits:

  1. **Step 1 "Announce task"** — replace:
     ```
     1. **Announce task**: "Working on: [Task N] — {task description}"
     ```
     with:
     ```
     1. **Announce task**: Print `[T{N}/{total}] {task description}` — where N is
        the 1-based task index and total is the count of tasks in the plan.
     ```

  2. **Step 3 RED** — add emit line at the start of the step:
     ```
     3. **เขียน test ที่ล้มเหลวก่อน (RED)**
        Print: `→ RED`
        Invoke `Skill(zie-framework:test-pyramid)`...
     ```

  3. **Step 4 GREEN** — add emit line:
     ```
     4. **เขียน code ให้ผ่าน test (GREEN)**
        Print: `→ GREEN`
        เขียน code น้อยที่สุด...
     ```

  4. **Step 5 REFACTOR** — add emit line:
     ```
     5. **ปรับปรุง code โดยไม่ทำให้ test พัง (REFACTOR)**
        Print: `→ REFACTOR`
        ลด duplication...
     ```

  5. **Step 7 "บันทึก task เสร็จ"** — append after the existing update instructions:
     ```
        Print: `✓ done — {remaining} remaining`
     ```

  6. **After step 7, before step 8**, insert new checkpoint step:
     ```
     7a. **Checkpoint** (every 3 tasks or at the halfway point):
         Print:
         ```
         Checkpoint [{N}/{total}]: completed: {done_list} | remaining: {remaining_list}
         ```
     ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Read the full modified steps 1–8 block. Confirm all existing logic (TaskUpdate,
  plan file mark, memory write) is intact. Confirm no duplicate emit lines.
  Run: `make test-unit` — still PASS

---

## Task 2: Add progress counters to `commands/zie-audit.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-audit.md` contains `[Phase 1/5]` phase counter text
- Contains `Agent` completion marker text (e.g., `Agent A` + check/done indicator)
- Contains `[Research ` search counter notation
- Contains `phases complete` end summary text

**Counter strings to add:**
- Each phase heading: emit `[Phase N/5] {phase name}` at the start of Phase 1–5
- Per parallel agent completion: emit `  Agent {X} ({Domain}) ✓` when each agent returns
- Per web search in Phase 3: emit `[Research {N}/15]` before each `WebSearch` call
- End of Phase 5: emit `5 phases complete — {N} findings`

**Files:**
- Modify: `commands/zie-audit.md`
- Modify: `tests/unit/test_progress_visibility.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_progress_visibility.py — add after TestImplementProgress

  class TestAuditProgress:
      def test_phase_counter_present(self):
          text = (COMMANDS_DIR / "zie-audit.md").read_text()
          assert "[Phase 1/5]" in text, \
              "zie-audit.md must contain [Phase 1/5] counter"

      def test_agent_completion_marker_present(self):
          text = (COMMANDS_DIR / "zie-audit.md").read_text()
          assert "Agent A" in text and "✓" in text, \
              "zie-audit.md must contain Agent A completion marker"

      def test_research_counter_present(self):
          text = (COMMANDS_DIR / "zie-audit.md").read_text()
          assert "[Research " in text, \
              "zie-audit.md must contain [Research N/15] counter"

      def test_phases_complete_summary_present(self):
          text = (COMMANDS_DIR / "zie-audit.md").read_text()
          assert "phases complete" in text, \
              "zie-audit.md must contain 'phases complete' end summary"
  ```
  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**
  In `commands/zie-audit.md`, apply these targeted edits:

  1. **Phase 1 heading** — prepend emit to `## Phase 1 — Project Intelligence`:
     ```
     Print: `[Phase 1/5] Project Intelligence`
     ```
     Add as the first instruction line under the Phase 1 heading.

  2. **Phase 2 heading** — prepend emit:
     ```
     Print: `[Phase 2/5] Parallel Internal Analysis`
     ```
     Add as the first instruction line under `## Phase 2 — Parallel Internal Analysis`.

  3. **Phase 2 agent completions** — after each agent definition block (Agent A
     through Agent E), note that on return each agent should emit:
     `  Agent A (Security) ✓`, `  Agent B (Lean) ✓`, etc.
     Add a closing note after the Agent E block:
     ```
     As each agent returns, print: `  Agent {X} ({Domain}) ✓`
     ```

  4. **Phase 3 heading** — prepend emit:
     ```
     Print: `[Phase 3/5] Dynamic External Research`
     ```

  5. **Phase 3 WebSearch loop** — add counter emit before each search:
     ```
     Before each `WebSearch` call, print: `[Research {N}/15]` where N is the
     1-based index of the current query.
     ```
     Add this as an instruction in the Phase 3 search loop paragraph.

  6. **Phase 4 heading** — prepend emit:
     ```
     Print: `[Phase 4/5] Synthesis`
     ```

  7. **Phase 5 heading** — prepend emit:
     ```
     Print: `[Phase 5/5] Report + Backlog Selection`
     ```

  8. **End of Phase 5 report** — after printing the full report block, add:
     ```
     Print: `5 phases complete — {N} findings ({critical} critical, {high} high)`
     ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Read the full Phase 1–5 sections. Confirm all existing logic (research_profile
  construction, agent spawn, WebSearch cap, synthesis rules, backlog selection)
  is intact. No duplicate headings introduced.
  Run: `make test-unit` — still PASS

---

## Task 3: Add progress counters to `commands/zie-release.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-release.md` contains `[Gate 1/7]` gate counter text
- Contains `[Gate 2/7]` to confirm counter pattern is applied to all gates
- Contains `[Step ` post-gate step counter notation
- Gate failure lines include the gate number (e.g., `Gate 1 FAILED` — already present, verify retained)

**Counter strings to add:**
- Each gate check: emit `[Gate N/7]` at the start of each of the 7 gate sections
  (Unit Tests = Gate 1, Integration = Gate 2, E2E = Gate 3, Visual = Gate 4,
  TODOs/Secrets = Gate 5, Docs sync = Gate 6, Code diff = Gate 7)
- Post-gate release steps (steps 1–12 of the "All Gates Passed" section): emit
  `[Step N/12]` at the start of each numbered step

**Files:**
- Modify: `commands/zie-release.md`
- Modify: `tests/unit/test_progress_visibility.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_progress_visibility.py — add after TestAuditProgress

  class TestReleaseProgress:
      def test_gate_1_counter_present(self):
          text = (COMMANDS_DIR / "zie-release.md").read_text()
          assert "[Gate 1/7]" in text, \
              "zie-release.md must contain [Gate 1/7] counter"

      def test_gate_2_counter_present(self):
          text = (COMMANDS_DIR / "zie-release.md").read_text()
          assert "[Gate 2/7]" in text, \
              "zie-release.md must contain [Gate 2/7] counter"

      def test_step_counter_present(self):
          text = (COMMANDS_DIR / "zie-release.md").read_text()
          assert "[Step " in text, \
              "zie-release.md must contain [Step N/12] post-gate step counter"
  ```
  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**
  In `commands/zie-release.md`, apply these targeted edits:

  1. **Gate 1 — Unit Tests** — add emit as first line under `### ตรวจสอบ: Unit Tests`:
     ```
     Print: `[Gate 1/7] Unit Tests`
     ```

  2. **Gate 2 — Integration Tests** — add emit under `### ตรวจสอบ: Integration Tests`:
     ```
     Print: `[Gate 2/7] Integration Tests`
     ```

  3. **Gate 3 — E2E Tests** — add emit under `### ตรวจสอบ: E2E Tests`:
     ```
     Print: `[Gate 3/7] E2E Tests`
     ```

  4. **Gate 4 — Visual** — add emit under `### ตรวจสอบ: Visual`:
     ```
     Print: `[Gate 4/7] Visual`
     ```

  5. **Gate 5 — TODOs และ Secrets** — add emit under `### ตรวจสอบ: TODOs และ Secrets`:
     ```
     Print: `[Gate 5/7] TODOs + Secrets`
     ```

  6. **Gate 6 — Docs sync** — add emit under `### ตรวจสอบ: Docs sync`:
     ```
     Print: `[Gate 6/7] Docs Sync`
     ```

  7. **Gate 7 — Code diff** — add emit under `### ตรวจสอบ: Code diff ก่อน merge`:
     ```
     Print: `[Gate 7/7] Code Diff`
     ```

  8. **Post-gate steps** — prefix each of the 12 numbered steps in
     `## All Gates Passed — Release` with `[Step N/12]`:
     - Step 1 (Suggest version bump): `Print: '[Step 1/12] Suggest version bump'`
     - Step 2 (Bump VERSION): `Print: '[Step 2/12] Bump VERSION'`
     - Step 3 (Update ROADMAP): `Print: '[Step 3/12] Update ROADMAP'`
     - Step 4 (Draft CHANGELOG): `Print: '[Step 4/12] Draft CHANGELOG entry'`
     - Step 5 (Pre-flight): `Print: '[Step 5/12] Pre-flight check'`
     - Step 6 (Commit release): `Print: '[Step 6/12] Commit release files'`
     - Step 7 (Readiness gate): `Print: '[Step 7/12] Readiness gate'`
     - Step 8 (Delegate publish): `Print: '[Step 8/12] make release'`
     - Step 9 (Store in brain): `Print: '[Step 9/12] Store in brain'`
     - Step 10 (Auto-run retro): `Print: '[Step 10/12] Run /zie-retro'`
     - Step 11 (Final print): `Print: '[Step 11/12] Print release summary'`
     (Note: the existing numbered list only goes to 11 items; total is 11 — use
     `[Step N/11]` to match actual count. Adjust test accordingly.)

  **Correction:** Count actual numbered items in `## All Gates Passed — Release`:
  steps 1–10 + final print step = 11 steps total. Use `[Step 1/11]` through
  `[Step 11/11]`. Update tests to assert `[Step 1/11]` instead of `[Step 1/12]`.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Read all 7 gate sections and the "All Gates Passed" section. Confirm all
  existing bash blocks, failure STOP instructions, and gate logic are intact.
  Confirm gate counter total matches actual gate count.
  Run: `make test-unit` — still PASS

---

## Task 4: Add progress counters to `commands/zie-plan.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-plan.md` contains `[Plan ` counter notation for per-slug progress
- Contains reviewer pass marker text (e.g., `plan-reviewer pass`)
- Contains `Plans processed:` summary (already present — verify retained)

**Counter strings to add:**
- Per-slug agent work: emit `[Plan {N}/{M}] {slug} — drafting...` when each
  parallel agent starts, `[Plan {N}/{M}] {slug} ✓` when it returns
- Reviewer gate: emit `  plan-reviewer pass {attempt}...` before each reviewer
  invocation, `  ✅` on approved or `  ❌ issues — fixing...` on issues found

**Files:**
- Modify: `commands/zie-plan.md`
- Modify: `tests/unit/test_progress_visibility.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_progress_visibility.py — add after TestReleaseProgress

  class TestPlanProgress:
      def test_plan_counter_present(self):
          text = (COMMANDS_DIR / "zie-plan.md").read_text()
          assert "[Plan " in text, \
              "zie-plan.md must contain [Plan N/M] counter notation"

      def test_reviewer_pass_marker_present(self):
          text = (COMMANDS_DIR / "zie-plan.md").read_text()
          assert "plan-reviewer pass" in text, \
              "zie-plan.md must contain 'plan-reviewer pass' marker"
  ```
  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**
  In `commands/zie-plan.md`, apply these targeted edits:

  1. **Multi-slug agent spawn** — in `## ร่าง plan สำหรับ slug ที่เลือก`, step 2
     (parallel agents block), add emit instructions:
     ```
     Before spawning each agent, print: `[Plan {N}/{M}] {slug} — drafting...`
     When each agent returns, print: `[Plan {N}/{M}] {slug} ✓`
     ```

  2. **Single-slug path** — in step 3 (single slug inline), add:
     ```
     Print: `[Plan 1/1] {slug} — drafting...`
     On completion: `[Plan 1/1] {slug} ✓`
     ```

  3. **plan-reviewer gate** — in `## plan-reviewer gate`, step 1, before the
     reviewer invocation, add:
     ```
     Print: `  plan-reviewer pass {attempt}...`
     ```
     After reviewer returns:
     - Approved: Print `  ✅`
     - Issues found: Print `  ❌ issues — fixing...`

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Read the full parallel-agent block and plan-reviewer gate section. Confirm
  max-4-agents cap, fix-iterate loop (max 3), and Zie approval prompt are intact.
  Run: `make test-unit` — still PASS

---

## Task 5: Add progress markers to `commands/zie-resync.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-resync.md` contains `Exploring codebase...` start marker
- Contains `Explored` completion text (e.g., `✓ Explored N files`)
- The existing `"Rescanning codebase..."` print (step 1) is retained

**Counter strings to add:**
- Before the `Agent(subagent_type=Explore)` invocation: emit `Exploring codebase...`
- After agent returns: emit `✓ Explored {N} files — drafting knowledge updates`

**Files:**
- Modify: `commands/zie-resync.md`
- Modify: `tests/unit/test_progress_visibility.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_progress_visibility.py — add after TestPlanProgress

  class TestResyncProgress:
      def test_exploring_marker_present(self):
          text = (COMMANDS_DIR / "zie-resync.md").read_text()
          assert "Exploring codebase" in text, \
              "zie-resync.md must contain 'Exploring codebase...' start marker"

      def test_explored_completion_marker_present(self):
          text = (COMMANDS_DIR / "zie-resync.md").read_text()
          assert "Explored" in text, \
              "zie-resync.md must contain 'Explored' completion marker"
  ```
  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**
  In `commands/zie-resync.md`, apply these targeted edits:

  1. **Step 2 — Invoke Agent** — prepend before the `Invoke Agent(subagent_type=Explore):` line:
     ```
     Print: `Exploring codebase...`
     ```

  2. **Step 3 — After agent returns** — add emit at the start of step 3:
     ```
     Print: `✓ Explored {N} files — drafting knowledge updates`
     (N = count of files returned in agent report; use "N" literally if count
     is not surfaced by the agent)
     ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Read steps 1–10. Confirm `"Rescanning codebase..."` (step 1 existing print)
  is still present. Confirm agent exclusion list, doc draft, and hash update
  steps are untouched.
  Run: `make test-unit` — still PASS

---

## Task 6: Add progress counters to `commands/zie-retro.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-retro.md` contains `[ADR ` counter notation
- Contains `Analyzing git log` phase marker text
- Contains `Updating knowledge docs` phase marker text

**Counter strings to add:**
- In `### บันทึก ADRs` loop: emit `[ADR {N}/{total}] {slug}` before creating each ADR file
- Phase markers:
  - Start of `### รวบรวม context`: emit `Analyzing git log...`
  - End of `### รวบรวม context` (after brain recall): emit `✓ context ready`
  - Start of `### อัปเดต project knowledge`: emit `Updating knowledge docs...`
  - End of `### อัปเดต project knowledge`: emit `✓ knowledge docs updated`

**Files:**
- Modify: `commands/zie-retro.md`
- Modify: `tests/unit/test_progress_visibility.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_progress_visibility.py — add after TestResyncProgress

  class TestRetroProgress:
      def test_adr_counter_present(self):
          text = (COMMANDS_DIR / "zie-retro.md").read_text()
          assert "[ADR " in text, \
              "zie-retro.md must contain [ADR N/M] counter notation"

      def test_analyzing_git_log_marker_present(self):
          text = (COMMANDS_DIR / "zie-retro.md").read_text()
          assert "Analyzing git log" in text, \
              "zie-retro.md must contain 'Analyzing git log' phase marker"

      def test_updating_knowledge_docs_marker_present(self):
          text = (COMMANDS_DIR / "zie-retro.md").read_text()
          assert "Updating knowledge docs" in text, \
              "zie-retro.md must contain 'Updating knowledge docs' phase marker"
  ```
  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**
  In `commands/zie-retro.md`, apply these targeted edits:

  1. **`### รวบรวม context` section** — add at the very start of the section body:
     ```
     Print: `Analyzing git log...`
     ```
     Add after the brain recall step (step 1 in this section, or after the
     subagent activity read if memory disabled):
     ```
     Print: `✓ context ready`
     ```

  2. **`### บันทึก ADRs` section** — in the "For each significant architectural
     decision" loop, prepend before creating each ADR file:
     ```
     Print: `[ADR {N}/{total}] {slug}` — where N is the 1-based index of the
     current ADR being written and total is the count of decisions identified.
     ```

  3. **`### อัปเดต project knowledge` section** — add at the start:
     ```
     Print: `Updating knowledge docs...`
     ```
     Add at the end (after the memory write instruction):
     ```
     Print: `✓ knowledge docs updated`
     ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Read all five section bodies. Confirm subagent activity log parsing, ADR
  template, ROADMAP update, and brain storage steps are untouched.
  Run: `make test-unit` — still PASS

---

*Commit: `git add commands/zie-implement.md commands/zie-audit.md commands/zie-release.md commands/zie-plan.md commands/zie-resync.md commands/zie-retro.md tests/unit/test_progress_visibility.py && git commit -m "feat: progress-visibility"`*
