---
approved: true
approved_at: 2026-04-04
backlog: backlog/phase-prose-cleanup.md
---

# Phase/Step Explanatory Prose Cleanup — Implementation Plan

**Goal:** Delete ~600–700 words of redundant explanatory prose from 6 skill/command files without changing any behaviour.
**Architecture:** Surgical delete-only pass — no restructuring, no logic changes. Each file is edited independently; `make test-unit` runs after each edit to catch broken test assertions before moving to the next file. tdd-loop and debug receive an extra consolidation step: inline "Never" rules that duplicate the `## กฎที่ต้องทำตาม` block are removed from step bodies.
**Tech Stack:** Markdown file editing · pytest (via `make test-unit`) · wc -w for word-count verification.

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/tdd-loop/SKILL.md` | Remove inline "Never" duplicates from step bodies |
| Modify | `skills/debug/SKILL.md` | Remove inline "Never" duplicates from step bodies |
| Modify | `skills/zie-audit/SKILL.md` | Remove explanatory restatement prose after phase headers |
| Modify | `commands/sprint.md` | Remove explanatory paragraphs before imperative steps in phase headers |
| Modify | `commands/retro.md` | Remove narrative sentences before step lists in section headers |
| Modify | `commands/release.md` | Remove explanatory prose before gate steps in phase headers |

---

## Task 1: Baseline word count + test-suite green check

**Acceptance Criteria:**
- `make test-unit` exits 0 on the unmodified codebase.
- Baseline word counts for all 6 files are recorded (used for final verification).

**Files:**
- No file modifications in this task — read and run only.

- [ ] **Step 1: Write failing tests (RED)**
  No new tests needed — this task is a pre-flight check only. There is no RED phase.

- [ ] **Step 2: Implement (GREEN)**

  ```bash
  make test-unit
  ```

  Must exit 0. If any tests fail, stop and fix before proceeding.

  Record baseline counts:

  ```bash
  wc -w skills/tdd-loop/SKILL.md skills/debug/SKILL.md skills/zie-audit/SKILL.md \
         commands/sprint.md commands/retro.md commands/release.md
  ```

  Save total for comparison in Task 6.

- [ ] **Step 3: Refactor**
  N/A — no code written.
  Run: `make test-unit` — still PASS

---

## Task 2: Clean tdd-loop/SKILL.md and debug/SKILL.md

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `skills/tdd-loop/SKILL.md`: no "Never" sentences appear inside the RED/GREEN/REFACTOR step bodies; all "Never" rules exist only in `## กฎที่ต้องทำตาม`.
- `skills/debug/SKILL.md`: same — no "Never" sentences inside `## Steps` phase bodies; rules block unchanged.
- `make test-unit` exits 0 after both edits.

**Files:**
- Modify: `skills/tdd-loop/SKILL.md`
- Modify: `skills/debug/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**

  Inspect both files first:

  ```bash
  grep -n "Never" skills/tdd-loop/SKILL.md
  grep -n "Never" skills/debug/SKILL.md
  ```

  Confirm: are any "Never" lines inside the phase step bodies (not inside `## กฎที่ต้องทำตาม`)?
  - tdd-loop current state: all "Never" rules are already consolidated in `## กฎที่ต้องทำตาม` — no inline duplicates present. Skip edit if grep shows zero "Never" lines outside the rules block.
  - debug current state: same check.

  No test code to write — this is a prose-only delete. The existing `test_tdd_loop_skill.py` (which asserts on `### RED`, `### GREEN`, `### REFACTOR`, `make test-fast`, `make test-ci`) acts as the regression harness.

  Run: `make test-unit` — must PASS (baseline confirmed in Task 1)

- [ ] **Step 2: Implement (GREEN)**

  For `skills/tdd-loop/SKILL.md`:
  - Re-read file fully.
  - Identify any "Never do X" sentence that appears inside a step body AND is already present verbatim in `## กฎที่ต้องทำตาม`.
  - Delete only those inline duplicates. If none found → no edit needed.

  For `skills/debug/SKILL.md`:
  - Re-read file fully.
  - Same check: identify "Never" sentences inside `## Steps` phase bodies that duplicate the rules block.
  - Delete only those inline duplicates. If none found → no edit needed.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Verify rules blocks are complete and no constraint was accidentally removed.
  Run: `make test-unit` — still PASS

---

## Task 3: Clean skills/zie-audit/SKILL.md

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- Explanatory restatement sentences immediately after each phase header in `skills/zie-audit/SKILL.md` are deleted where the first imperative step already covers the same content.
- `active_agents` logic and functional content in Phase 2 are untouched.
- `make test-unit` exits 0 after edit.

**Files:**
- Modify: `skills/zie-audit/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**

  Identify test files that assert on zie-audit SKILL.md content:

  ```bash
  grep -rn "SKILL\|zie.audit" tests/unit/test_zie_audit.py tests/unit/test_zie_audit_v2.py \
       tests/unit/test_zie_audit_enhancements.py tests/unit/test_zie_audit_shared_context.py \
       tests/unit/test_audit_parallel_research.py tests/unit/test_audit_mcp_check.py | grep "assert"
  ```

  For each asserted string, confirm it is NOT part of the explanatory prose being deleted.
  If any assertion matches targeted prose → that prose must be kept (per spec edge case rule).

  Run: `make test-unit` — must PASS

- [ ] **Step 2: Implement (GREEN)**

  Re-read `skills/zie-audit/SKILL.md` fully.

  Delete explanatory restatement prose immediately following phase headers where the first imperative step already covers the same ground. Specifically:
  - **Phase 2** header area: remove any paragraph that restates "Spawn 5 parallel agents" if the `Spawn 5 parallel agents via \`Agent\` tool.` line in the body already says it.
  - Apply the same check to all other phases (Phase 1, Phase 3, etc.).
  - Retain: `active_agents` logic sentence, `--focus` conditional behavior, all imperative steps, all structural headers.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Spot-check: read changed sections to confirm no functional constraint was lost.
  Run: `make test-unit` — still PASS

---

## Task 4: Clean commands/sprint.md

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- Explanatory paragraphs between phase headers and their first imperative step in `commands/sprint.md` are deleted.
- All imperative steps, phase names, progress-reporting rules, and logic are intact.
- `make test-unit` exits 0 after edit.

**Files:**
- Modify: `commands/sprint.md`

- [ ] **Step 1: Write failing tests (RED)**

  Check which test assertions target sprint.md content:

  ```bash
  grep -rn "sprint" tests/unit/test_zie_sprint.py tests/unit/test_zie_sprint_docs.py \
       tests/unit/test_zie_sprint_phase3.py tests/unit/test_intent_sdlc_sprint.py | grep "assert"
  ```

  Cross-reference each asserted string against prose candidates for deletion.
  Any asserted string in candidate prose → keep that line.

  Run: `make test-unit` — must PASS

- [ ] **Step 2: Implement (GREEN)**

  Re-read `commands/sprint.md` fully.

  For each `## PHASE N:` header:
  - Read from header to the first numbered step (`1.` or `For each`).
  - If there is an explanatory paragraph (not the `TaskCreate` line, not argument-parsing code) between the header and first imperative step that merely restates what the first step says → delete those sentences only.
  - Keep: `TaskCreate` lines, code blocks, `TaskUpdate` lines, progress bar print statements, all logic.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Verify phase boundaries and progress reporting rules are intact.
  Run: `make test-unit` — still PASS

---

## Task 5: Clean commands/retro.md and commands/release.md

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- Explanatory narrative sentences between section headers and their first imperative step in `commands/retro.md` are deleted where the step already covers the same ground.
- Same for `commands/release.md` phase headers.
- `make test-unit` exits 0 after both edits.

**Files:**
- Modify: `commands/retro.md`
- Modify: `commands/release.md`

- [ ] **Step 1: Write failing tests (RED)**

  Check test assertions for both files:

  ```bash
  grep -rn "retro\|release" \
       tests/unit/test_retro_parallel.py \
       tests/unit/test_hybrid_release.py \
       tests/unit/test_zie_release_parallel_gates.py \
       tests/unit/test_release_auto_version.py \
       tests/unit/test_retro_self_tuning.py | grep "assert" | head -40
  ```

  Cross-reference each asserted string against prose candidates for deletion.
  Any asserted string → keep that line.

  Run: `make test-unit` — must PASS

- [ ] **Step 2: Implement (GREEN)**

  `commands/retro.md`:
  - Re-read file fully.
  - For each `###` section header: check whether there is a narrative sentence between the header and the first numbered step that restates what step 1 already says.
  - Delete those sentences only. Keep: all numbered steps, injected bash blocks (`!git ...`), `zie_memory` conditionals.

  `commands/release.md`:
  - Re-read file fully.
  - For each gate section header: check whether there is explanatory prose before the first numbered or bash step that restates what the step already says.
  - Delete those sentences only. Keep: all steps, bash blocks, conditional logic, gate numbers.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Read changed sections to confirm no constraint was accidentally lost.
  Run: `make test-unit` — still PASS

---

## Task 6: Final word-count verification

<!-- depends_on: Task 2, Task 3, Task 4, Task 5 -->

**Acceptance Criteria:**
- Total word count across all 6 files has decreased by 600–700 words vs baseline recorded in Task 1.
- `make test-unit` exits 0.

**Files:**
- No file modifications — verification only.

- [ ] **Step 1: Write failing tests (RED)**
  No new test code needed — existing suite is the gate.

- [ ] **Step 2: Implement (GREEN)**

  ```bash
  wc -w skills/tdd-loop/SKILL.md skills/debug/SKILL.md skills/zie-audit/SKILL.md \
         commands/sprint.md commands/retro.md commands/release.md
  ```

  Compare total to baseline. Expected reduction: 600–700 words.
  If reduction is < 300 words → review Tasks 2–5 for missed prose.
  If reduction is > 800 words → review for accidental deletion of functional content.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  N/A — no code written.
  Run: `make test-unit` — still PASS
