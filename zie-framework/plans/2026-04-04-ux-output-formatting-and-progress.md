---
approved: true
approved_at: 2026-04-04
backlog: backlog/ux-output-formatting-and-progress.md
---

# UX Output Formatting and Progress Visibility — Implementation Plan

**Goal:** Add consistent phase/step counters, Unicode progress bars, TaskCreate/TaskUpdate
integration, and a lightweight ETA signal to zie-implement, zie-audit, zie-resync, and
zie-sprint; document the hook INFO output convention in CLAUDE.md.

**Architecture:** All changes are additive output-only edits to four command `.md` files and
one documentation file. No hook Python code is touched. The phase-count ETA signal is
derived purely from the phase counter already being printed — no clock access needed.

**Tech Stack:** Markdown (commands), CLAUDE.md (documentation)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-implement.md` | Add `[T{N}/{total}]` header, `→ RED/GREEN/REFACTOR` markers, `✓ T{N} done — {remaining} remaining` footer per task |
| Modify | `commands/zie-audit.md` | Add `[Phase N/M]` header at each audit phase start, `Agent {X} (Domain) ✓` per spawned agent, `[Research {N}/15]` per search call |
| Modify | `commands/zie-resync.md` | Replace bare `"Exploring codebase..."` with `[Exploring codebase...]` header; add completion summary line |
| Modify | `commands/zie-sprint.md` | Add `TaskCreate`/`TaskUpdate` per phase, Unicode progress bar after each phase, phase-count ETA signal |
| Modify | `CLAUDE.md` | Add Hook Output Convention subsection; extend Hook Error Handling Convention with INFO vs error distinction |

---

## Task 1: zie-implement — Task counter + phase markers

**Acceptance Criteria:**
- `zie-implement` prints `[T{N}/{total}]` before starting each task
- `zie-implement` prints `→ RED`, `→ GREEN`, `→ REFACTOR` phase markers within each task's TDD loop
- `zie-implement` prints `✓ T{N} done — {remaining} remaining` after each task completes

**Files:**
- Modify: `commands/zie-implement.md`

- [ ] **Step 1: Write failing tests (RED)**

  Test file: `tests/integration/test_commands_md_lint.py` — add assertions for the
  three output strings in `zie-implement.md`:

  ```python
  def test_zie_implement_task_counter_header(zie_implement_md):
      assert "[T{N}/{total}]" in zie_implement_md, (
          "zie-implement must print [T{N}/{total}] before each task"
      )

  def test_zie_implement_phase_markers(zie_implement_md):
      for marker in ["→ RED", "→ GREEN", "→ REFACTOR"]:
          assert marker in zie_implement_md, (
              f"zie-implement must print phase marker: {marker}"
          )

  def test_zie_implement_task_done_footer(zie_implement_md):
      assert "{remaining} remaining" in zie_implement_md, (
          "zie-implement must print '✓ T{N} done — {remaining} remaining' after each task"
      )
  ```

  Add fixture in conftest if not present:

  ```python
  @pytest.fixture
  def zie_implement_md():
      path = Path(__file__).parents[2] / "commands" / "zie-implement.md"
      return path.read_text()
  ```

  Run: `make test-unit` — must FAIL (strings not yet present)

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-implement.md`, Task Loop section, update the step list:

  - Step 1 already has: `Print [T{N}/{total}] {description}` — verify it reads exactly
    `[T{N}/{total}]` (it currently does per line 61). If already present, confirm test passes.

  - Within the TDD loop step, add explicit phase marker prints. The tdd-loop skill handles
    RED/GREEN/REFACTOR internally, but the command should instruct Claude to print markers
    before invoking each phase. Add to Step 2 in the Task Loop:

    ```markdown
    2. **→ TDD loop** — Print `→ RED` before writing tests; print `→ GREEN` before
       implementing; print `→ REFACTOR` before cleanup. Then invoke
       `Skill(zie-framework:tdd-loop)`. Follow it exactly.
    ```

  - Step 6 currently reads:
    `TaskUpdate → completed. Mark [x] in plan. Print ✓ done — {remaining} remaining.`
    Update to include task number:
    `TaskUpdate → completed. Mark [x] in plan. Print \`✓ T{N} done — {remaining} remaining\`.`

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  - Verify the three marker strings are on distinct lines in the command for readability.
  - Ensure no duplicate or conflicting output instructions exist in the Task Loop.

  Run: `make test-unit` — still PASS

---

## Task 2: zie-audit — Phase headers + per-agent/search counters

<!-- depends_on: none -->

**Acceptance Criteria:**
- `zie-audit` prints `[Phase 1/4]` … `[Phase 4/4]` (or dynamic M) at each phase start
- `zie-audit` prints `Agent {X} (Domain) ✓` after each spawned agent completes
- `zie-audit` prints `[Research {N}/15]` before each WebSearch call (max 15 cap)

**Files:**
- Modify: `commands/zie-audit.md`

- [ ] **Step 1: Write failing tests (RED)**

  Add to `tests/integration/test_commands_md_lint.py`:

  ```python
  def test_zie_audit_phase_header(zie_audit_md):
      assert "[Phase" in zie_audit_md, (
          "zie-audit must print [Phase N/M] headers"
      )

  def test_zie_audit_agent_completion_marker(zie_audit_md):
      assert "Agent" in zie_audit_md and "✓" in zie_audit_md, (
          "zie-audit must print Agent {X} (Domain) ✓ per spawned agent"
      )

  def test_zie_audit_research_counter(zie_audit_md):
      assert "[Research" in zie_audit_md, (
          "zie-audit must print [Research {N}/15] per search call"
      )

  @pytest.fixture
  def zie_audit_md():
      path = Path(__file__).parents[2] / "commands" / "zie-audit.md"
      return path.read_text()
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-audit.md`:

  1. After the `## Phase 1 — Context Bundle` heading, add a print instruction:
     `Print: \`[Phase 1/4] Context Bundle\``

  2. After the `## Phase 2 — Parallel Dimension Scan` heading, add:
     `Print: \`[Phase 2/4] Parallel Dimension Scan (active agents: {N})\``

     After each agent result arrives, print:
     `\`Agent {X} ({Domain}) ✓\`` (e.g. `Agent 1 (Security/Deps) ✓`)

  3. Before each WebSearch call (capped at 15), add:
     `Print: \`[Research {N}/15]\`` (increment N per call)

  4. After synthesis phase heading, add:
     `Print: \`[Phase 3/4] Synthesis\``

  5. After final output / findings section heading, add:
     `Print: \`[Phase 4/4] Findings Output\``

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  - Verify phase count M is dynamic where phases differ (e.g. `--focus` flag reduces agents).
    Update instructions to say: `M = total active phases (minimum 3: context, scan, output)`.
  - Trim any duplicate print instructions.

  Run: `make test-unit` — still PASS

---

## Task 3: zie-resync — Structured start + completion summary

<!-- depends_on: none -->

**Acceptance Criteria:**
- `zie-resync` prints `[Exploring codebase...]` (bracketed) at scan start
- `zie-resync` prints a completion summary line with knowledge_hash prefix and synced_at

**Files:**
- Modify: `commands/zie-resync.md`

- [ ] **Step 1: Write failing tests (RED)**

  Add to `tests/integration/test_commands_md_lint.py`:

  ```python
  def test_zie_resync_bracketed_start(zie_resync_md):
      assert "[Exploring codebase...]" in zie_resync_md, (
          "zie-resync must print [Exploring codebase...] (bracketed)"
      )

  def test_zie_resync_completion_summary(zie_resync_md):
      assert "knowledge_hash" in zie_resync_md and "synced_at" in zie_resync_md, (
          "zie-resync must print completion summary with knowledge_hash and synced_at"
      )

  @pytest.fixture
  def zie_resync_md():
      path = Path(__file__).parents[2] / "commands" / "zie-resync.md"
      return path.read_text()
  ```

  Run: `make test-unit` — must FAIL (step 1 prints bare `"Exploring codebase..."`)

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-resync.md`:

  1. Step 1 currently reads `Print: "Exploring codebase..."` — change to:
     `Print: \`[Exploring codebase...]\``

  2. The completion block in step 10 already prints `knowledge_hash` and `synced_at` —
     verify the test passes. If step 2 print (`"✓ Explored. Building knowledge drafts..."`)
     needs a bracketed form too, update to `[✓ Explored — building knowledge drafts...]`.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  - Confirm step 2 print instruction (`✓ Explored...`) is consistent with bracketed style.
  - No other changes needed (completion summary already exists in step 10).

  Run: `make test-unit` — still PASS

---

## Task 4: zie-sprint — TaskCreate/TaskUpdate + progress bar + phase-count ETA

<!-- depends_on: none -->

**Acceptance Criteria:**
- `zie-sprint` calls `TaskCreate` for each of the 5 phases before the phase begins
- `zie-sprint` calls `TaskUpdate` to mark each phase complete after it finishes
- `zie-sprint` prints a Unicode progress bar after each phase: `████████░░ {done}/{total} ({pct}%)`
- `zie-sprint` prints a phase-count ETA signal after each phase: `Phase {N}/{total} — {remaining} phases remaining`

**Files:**
- Modify: `commands/zie-sprint.md`

- [ ] **Step 1: Write failing tests (RED)**

  Add to `tests/integration/test_commands_md_lint.py`:

  ```python
  def test_zie_sprint_task_create_per_phase(zie_sprint_md):
      assert zie_sprint_md.count("TaskCreate") >= 5, (
          "zie-sprint must call TaskCreate for each of 5 phases"
      )

  def test_zie_sprint_task_update_per_phase(zie_sprint_md):
      assert zie_sprint_md.count("TaskUpdate") >= 5, (
          "zie-sprint must call TaskUpdate to mark each phase complete"
      )

  def test_zie_sprint_progress_bar(zie_sprint_md):
      assert "████" in zie_sprint_md or "{done}/{total}" in zie_sprint_md, (
          "zie-sprint must print Unicode progress bar"
      )

  def test_zie_sprint_eta_signal(zie_sprint_md):
      assert "phases remaining" in zie_sprint_md, (
          "zie-sprint must print phase-count ETA signal"
      )

  @pytest.fixture
  def zie_sprint_md():
      path = Path(__file__).parents[2] / "commands" / "zie-sprint.md"
      return path.read_text()
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-sprint.md`, update each PHASE section as follows:

  **PHASE 1 — SPEC ALL:**
  Add at the top of the phase:
  ```
  TaskCreate subject="Phase 1/5 — Spec All"
  ```
  Add at the bottom (after collecting results):
  ```
  TaskUpdate → Phase 1/5 complete
  Print: `████░░░░░░ 1/5 (20%) — Phase 1/5 — 4 phases remaining`
  ```

  **PHASE 2 — PLAN ALL:**
  ```
  TaskCreate subject="Phase 2/5 — Plan All"
  ...
  TaskUpdate → Phase 2/5 complete
  Print: `████████░░░░░░░░░░░░ 2/5 (40%) — Phase 2/5 — 3 phases remaining`
  ```

  **PHASE 3 — IMPLEMENT:**
  ```
  TaskCreate subject="Phase 3/5 — Implement"
  ...
  TaskUpdate → Phase 3/5 complete
  Print: `████████████░░░░░░░░ 3/5 (60%) — Phase 3/5 — 2 phases remaining`
  ```

  **PHASE 4 — BATCH RELEASE:**
  ```
  TaskCreate subject="Phase 4/5 — Release"
  ...
  TaskUpdate → Phase 4/5 complete
  Print: `████████████████░░░░ 4/5 (80%) — Phase 4/5 — 1 phase remaining`
  ```

  **PHASE 5 — SPRINT RETRO:**
  ```
  TaskCreate subject="Phase 5/5 — Retro"
  ...
  TaskUpdate → Phase 5/5 complete
  Print: `████████████████████ 5/5 (100%) — Sprint complete`
  ```

  Note: use `{done}/{total}` template notation in the instructions so Claude
  computes correct values at runtime. The static bar examples above are illustrative.
  Final instruction wording:
  ```
  Print progress bar: `{"█" * done_blocks}{"░" * empty_blocks} {done}/{total} ({pct}%)`
  Print ETA: `Phase {N}/{total} — {remaining} phases remaining` (or `Sprint complete` when done=total)
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  - Verify TaskCreate calls appear before phase work begins (not after).
  - Verify TaskUpdate calls appear after phase completion is confirmed.
  - Ensure progress bar and ETA are on separate lines for readability.
  - Confirm `phases remaining` string is present for ETA test.

  Run: `make test-unit` — still PASS

---

## Task 5: CLAUDE.md — Document hook INFO output convention

<!-- depends_on: none -->

**Acceptance Criteria:**
- `CLAUDE.md` contains a "Hook Output Convention" subsection under "Hook Context Hints"
- Convention states: `key: value` format applies to INFO-level output only
- "Hook Error Handling Convention" section notes the INFO vs error distinction
- Names `wip-checkpoint` and `task-completed-gate` as existing compliant hooks
- States no hook Python code changes are required

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Write failing tests (RED)**

  Add to `tests/integration/test_commands_md_lint.py` (or a dedicated
  `tests/integration/test_claude_md_conventions.py`):

  ```python
  from pathlib import Path

  def read_claude_md():
      return (Path(__file__).parents[2] / "CLAUDE.md").read_text()

  def test_claude_md_hook_output_convention_section():
      content = read_claude_md()
      assert "Hook Output Convention" in content, (
          "CLAUDE.md must have a Hook Output Convention subsection"
      )

  def test_claude_md_info_level_scope():
      content = read_claude_md()
      assert "INFO" in content or "INFO-level" in content, (
          "CLAUDE.md hook convention must specify INFO-level scope"
      )

  def test_claude_md_compliant_hooks_named():
      content = read_claude_md()
      assert "wip-checkpoint" in content and "task-completed-gate" in content, (
          "CLAUDE.md must name wip-checkpoint and task-completed-gate as compliant"
      )

  def test_claude_md_no_code_changes_needed():
      content = read_claude_md()
      assert "no" in content.lower() and "code changes" in content.lower(), (
          "CLAUDE.md must state no hook code changes are required"
      )
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `CLAUDE.md`, after the `## Hook Context Hints` section, add a new subsection:

  ```markdown
  ## Hook Output Convention

  All hooks emit INFO-level progress output using structured `[zie-framework] key: value`
  pairs. This applies to **INFO-level output only** — error output uses free-form messages
  (see Hook Error Handling Convention below).

  **Format:** `[zie-framework] <noun>: <value>`
  **Example:** `[zie-framework] wip: 1 task in progress`

  Existing compliant hooks (no code changes needed):
  - `wip-checkpoint` — already emits structured key: value for INFO output
  - `task-completed-gate` — already emits structured key: value for INFO output

  Future hooks must follow this convention for INFO-level output.
  ```

  In the existing `## Hook Error Handling Convention` section, add a note at the end:

  ```markdown
  **INFO vs error distinction:** The structured `[zie-framework] key: value` format
  (see Hook Output Convention above) applies to INFO-level progress output only.
  Error messages printed via the inner-operations tier keep their existing free-form
  format — no structured formatting required for error output.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  - Ensure the new subsection is placed between `## Hook Context Hints` and
    `## Hook Error Handling Convention` for logical flow.
  - Verify markdownlint passes: `make lint`.

  Run: `make test-unit` — still PASS

---

## Completion Checklist

- [ ] All 5 tasks implemented and tests passing
- [ ] `make test-unit` passes with no regressions
- [ ] `make lint` passes (markdownlint on all modified `.md` files)
- [ ] All Acceptance Criteria from spec verified
