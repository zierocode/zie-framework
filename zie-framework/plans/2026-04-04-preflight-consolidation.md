---
approved: true
approved_at: 2026-04-04
backlog: backlog/preflight-consolidation.md
---

# Preflight Consolidation — Implementation Plan

**Goal:** Replace ~1,500 words of duplicated pre-flight boilerplate across 10 commands with a single canonical reference, creating one source of truth for the standard 3-step guard.
**Architecture:** Create `zie-framework/project/command-conventions.md` as the canonical pre-flight doc. Each applicable command's `## ตรวจสอบก่อนเริ่ม` replaces only its standard 3-step guard with a one-line reference link; any unique steps stay inline. Tests asserting inline guard text are updated to assert the reference format instead.
**Tech Stack:** Markdown (commands, conventions doc), Python/pytest (test updates)

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `zie-framework/project/command-conventions.md` | Canonical 3-step pre-flight guard definition |
| Modify | `commands/spec.md` | Replace standard 3-step guard with reference line |
| Modify | `commands/plan.md` | Replace standard 3-step guard with reference line |
| Modify | `commands/fix.md` | Replace standard 3-step guard with reference line; keep ROADMAP WIP warn + memory recall inline |
| Modify | `commands/backlog.md` | Replace standard 2-step guard (steps 1–2) with reference line; keep memory recall step inline |
| Modify | `commands/resync.md` | Replace standard 2-step guard with reference line |
| Modify | `commands/chore.md` | No standard steps present; no change needed (slug-derive only) |
| Modify | `commands/hotfix.md` | No standard steps present; no change needed (slug-derive + optional .config read) |
| Modify | `commands/spike.md` | No standard steps present; no change needed (slug-derive only) |
| Modify | `commands/implement.md` | Replace steps 1–2 (zie-framework/ check + ROADMAP check) with reference line; keep live-context bash injections, agent-mode advisory, Ready-lane guard, WIP check, memory recall inline |
| No change | `commands/retro.md` | No standard guard; only git-log injections |
| No change | `commands/release.md` | Extended guard with VERSION/branch/playwright; only the zie-framework/ step is standard — keep inline for now (part of extended block) |
| No change | `commands/sprint.md` | Extended guard with branch/WIP checks; keep inline |
| No change | `commands/init.md` | Must NOT reference conventions doc (runs before zie-framework/ exists) |
| Modify | `tests/unit/test_e2e_optimization.py` | Update `test_backlog_preflight_is_concise` to accept reference line as 1 item |
| Modify | `tests/unit/test_implement_preflight.py` | Update guard-text assertions to match reference format |

---

## Task 1: Create `command-conventions.md` with canonical pre-flight protocol

**Acceptance Criteria:**
- File exists at `zie-framework/project/command-conventions.md`
- Contains a `## Pre-flight` anchor-able heading
- Defines all 3 standard steps: check `zie-framework/` exists, read `.config`, check ROADMAP Now lane
- Matches exact prose used in `spec.md` and `plan.md` today

**Files:**
- Create: `zie-framework/project/command-conventions.md`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_command_conventions.py
  from pathlib import Path

  CONVENTIONS = Path(__file__).parents[2] / "zie-framework" / "project" / "command-conventions.md"

  def test_conventions_file_exists():
      assert CONVENTIONS.exists(), "command-conventions.md must exist"

  def test_conventions_has_preflight_heading():
      text = CONVENTIONS.read_text()
      assert "## Pre-flight" in text, "command-conventions.md must have ## Pre-flight heading"

  def test_conventions_defines_3_steps():
      text = CONVENTIONS.read_text()
      assert "zie-framework/" in text
      assert ".config" in text
      assert "ROADMAP" in text

  def test_conventions_has_anchor():
      text = CONVENTIONS.read_text()
      # Markdown anchors are derived from headings; verify heading exists for deep-linking
      assert "pre-flight" in text.lower()
  ```

  Run: `make test-unit` — must FAIL (file does not exist yet)

- [ ] **Step 2: Implement (GREEN)**

  Create `zie-framework/project/command-conventions.md`:

  ```markdown
  # Command Conventions

  Shared protocol definitions referenced by all zie-framework commands.

  ---

  ## Pre-flight

  Every command that operates on an existing project runs these 3 steps before anything else:

  1. Check `zie-framework/` exists → if not, tell user to run `/init` first.
  2. Read `zie-framework/.config` → load project settings (project_type, zie_memory_enabled, etc.).
  3. Read `zie-framework/ROADMAP.md` → check Now lane.
     - If a `[ ]` item exists in Now → warn: "WIP active: `<feature>`. Starting a new task
       splits focus. Continue? (yes/no)"
     - If no ROADMAP.md found → STOP: "ROADMAP.md not found — run /init first."
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Verify heading and prose exactly match what `spec.md`/`plan.md` use today — no drift.
  Run: `make test-unit` — still PASS

---

## Task 2: Replace standard guard in `spec.md`, `plan.md`, `resync.md`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `spec.md` `## ตรวจสอบก่อนเริ่ม` body is exactly 1 line: the reference link
- `plan.md` `## ตรวจสอบก่อนเริ่ม` body is exactly 1 line: the reference link
- `resync.md` `## ตรวจสอบก่อนเริ่ม` body is exactly 1 line: the reference link
- Each file still has the Thai heading for structural consistency

**Files:**
- Modify: `commands/spec.md`
- Modify: `commands/plan.md`
- Modify: `commands/resync.md`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_preflight_consolidation.py
  from pathlib import Path

  COMMANDS_DIR = Path(__file__).parents[2] / "commands"

  REFERENCE_LINE = "command-conventions.md#pre-flight"

  def _preflight_body(cmd: str) -> str:
      text = (COMMANDS_DIR / f"{cmd}.md").read_text()
      start = text.find("## ตรวจสอบก่อนเริ่ม")
      assert start != -1, f"{cmd}.md must have ## ตรวจสอบก่อนเริ่ม"
      end = text.find("\n## ", start + 1)
      return text[start:end] if end != -1 else text[start:]

  def test_spec_preflight_is_reference():
      body = _preflight_body("spec")
      assert REFERENCE_LINE in body, "spec.md pre-flight must reference command-conventions.md#pre-flight"
      # Standard guard steps must NOT appear inline
      assert "Check `zie-framework/` exists" not in body

  def test_plan_preflight_is_reference():
      body = _preflight_body("plan")
      assert REFERENCE_LINE in body, "plan.md pre-flight must reference command-conventions.md#pre-flight"
      assert "Check `zie-framework/` exists" not in body

  def test_resync_preflight_is_reference():
      body = _preflight_body("resync")
      assert REFERENCE_LINE in body, "resync.md pre-flight must reference command-conventions.md#pre-flight"
      assert "Check `zie-framework/` exists" not in body
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In each of `spec.md`, `plan.md`, `resync.md`, replace the body of `## ตรวจสอบก่อนเริ่ม` (everything between that heading and the next `##`) with:

  ```
  See [Pre-flight standard](../zie-framework/project/command-conventions.md#pre-flight).
  ```

  Keep the Thai heading `## ตรวจสอบก่อนเริ่ม` intact.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Confirm no trailing blank lines are inconsistent. Run lint: `make lint`.
  Run: `make test-unit` — still PASS

---

## Task 3: Replace standard guard in `fix.md` and `backlog.md`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `fix.md`: standard 3-step guard replaced by reference line; ROADMAP WIP warn + memory recall remain inline (as steps 4+ or renumbered as custom steps)
- `backlog.md`: steps 1–2 (zie-framework/ check + .config read) replaced by reference line; memory recall step stays inline; pre-flight item count ≤ 3 (reference line = 1 item, memory recall = 1 item → total 2 ≤ 3)
- `test_backlog_preflight_is_concise` still passes

**Files:**
- Modify: `commands/fix.md`
- Modify: `commands/backlog.md`

- [ ] **Step 1: Write failing tests (RED)**

  Add to `tests/unit/test_preflight_consolidation.py`:

  ```python
  def test_fix_preflight_is_reference():
      body = _preflight_body("fix")
      assert REFERENCE_LINE in body, "fix.md pre-flight must reference command-conventions.md#pre-flight"
      assert "Check `zie-framework/` exists" not in body
      # Custom steps must remain
      assert "recall" in body or "memory" in body.lower()

  def test_backlog_preflight_is_reference():
      body = _preflight_body("backlog")
      assert REFERENCE_LINE in body, "backlog.md pre-flight must reference command-conventions.md#pre-flight"
      assert "Check `zie-framework/` exists" not in body
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  **fix.md:** Replace the standard 3-step block (steps 1–3: zie-framework/ check, .config read, ROADMAP Now check) with the reference line. Renumber remaining steps (WIP warn, memory recall) as steps 2–3.

  **backlog.md:** Replace steps 1–2 (zie-framework/ check, .config read) with the reference line. Keep memory recall as step 2.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Verify `test_backlog_preflight_is_concise` still passes (reference line counts as 1 numbered item — confirm it renders as a numbered list item or prose; adjust if test counts it).
  Run: `make test-unit` — still PASS

---

## Task 4: Replace standard guard steps in `implement.md`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `implement.md` pre-flight steps 1–2 (zie-framework/ exists, ROADMAP guard) replaced by reference line
- Live-context bash injections (`!git log`, `!git status`) remain at top of section
- Agent-mode advisory (step 0) remains inline
- Ready-lane guard, WIP check, uncommitted-work warn, memory recall all remain inline
- `test_implement_has_missing_roadmap_guard` still passes (ROADMAP missing case covered by referenced conventions doc or kept inline)
- `test_implement_has_ready_lane_guard` still passes

**Files:**
- Modify: `commands/implement.md`

- [ ] **Step 1: Write failing tests (RED)**

  Add to `tests/unit/test_preflight_consolidation.py`:

  ```python
  def test_implement_preflight_is_reference():
      body = _preflight_body("implement")
      assert REFERENCE_LINE in body, "implement.md pre-flight must reference command-conventions.md#pre-flight"
      # Standard step 1 inline text must be gone
      assert "Check `zie-framework/` exists" not in body

  def test_implement_retains_live_context():
      body = _preflight_body("implement")
      assert "git log" in body, "implement.md must retain live git log bash injection"
      assert "git status" in body

  def test_implement_retains_agent_advisory():
      body = _preflight_body("implement")
      assert "agent" in body.lower() or "zie-implement-mode" in body

  def test_implement_retains_ready_guard():
      body = _preflight_body("implement")
      assert "Ready" in body
  ```

  Also run existing tests to confirm they currently pass:
  ```
  make test-unit
  ```
  — new tests must FAIL, existing must still PASS

- [ ] **Step 2: Implement (GREEN)**

  In `implement.md`, within `## ตรวจสอบก่อนเริ่ม`:
  - Keep the `!git log -5 --oneline` and `!git status --short` bash lines at the top
  - Keep step 0 (agent-mode advisory) inline
  - Replace steps 1–2 (zie-framework/ check + ROADMAP exists/Now lane check) with the reference line: `See [Pre-flight standard](../zie-framework/project/command-conventions.md#pre-flight).`
  - Renumber remaining steps starting at 1: Ready-lane guard, WIP check, uncommitted work, .config read, memory recall

  Note: `test_implement_has_missing_roadmap_guard` asserts `"not found"` and `"/init"` appear in `implement.md`. The conventions doc will contain this text — but the test reads `implement.md` directly. Keep a brief inline note or ensure the Ready-lane guard section still contains `"not found"` / `"/init"` language to satisfy this test.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Review surrounding context to ensure advisory + reference line flow naturally.
  Run: `make test-unit` — still PASS

---

## Task 5: Update tests — remove stale inline-guard assertions

<!-- depends_on: Task 2, Task 3, Task 4 -->

**Acceptance Criteria:**
- `test_implement_preflight.py` assertions that check inline guard text are updated to pass with refactored `implement.md`
- `test_e2e_optimization.py::test_backlog_preflight_is_concise` still passes with reference line counting as ≤ 1 numbered item
- All existing tests continue to pass (`make test-unit` green)
- New `test_preflight_consolidation.py` tests all pass

**Files:**
- Modify: `tests/unit/test_implement_preflight.py`
- Modify: `tests/unit/test_e2e_optimization.py`

- [ ] **Step 1: Write failing tests (RED)**

  This task is driven by running the full suite and confirming no regressions exist. The "failing" state here is any test in the existing suite that was broken by Tasks 2–4.

  Run: `make test-unit` — identify any FAIL from existing tests

- [ ] **Step 2: Implement (GREEN)**

  For each broken assertion in `test_implement_preflight.py`:
  - `test_implement_has_missing_roadmap_guard`: if `"not found"` is no longer inline in `implement.md`, update assertion to also check `command-conventions.md` OR ensure implement.md retains the language (preferred: keep inline note in implement.md's Ready-lane guard per Task 4).
  - `test_implement_has_ready_lane_guard`: verify "Ready" + "empty"/"no approved plan" still present — should pass from Task 4.

  For `test_e2e_optimization.py::test_backlog_preflight_is_concise`:
  - The reference line is prose (not a numbered `1. ` item), so the item count check should still return ≤ 3. Verify by inspection. If the reference is written as a numbered item (`1. See [Pre-flight standard]...`), the count is 2 (reference + memory recall) ≤ 3 — still passes.
  - If any assertion is counting the reference line unexpectedly, adjust the test to exclude reference lines from the count or adjust the threshold comment.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Ensure test file docstrings reflect updated intent.
  Run: `make test-unit` — still PASS

---

## Task 6: Final verification — full suite + lint

<!-- depends_on: Task 5 -->

**Acceptance Criteria:**
- `make test-ci` passes (unit tests + coverage gate)
- `make lint` passes with zero violations
- All 5 commands' pre-flight sections contain the reference line
- `command-conventions.md` is present and linked correctly
- No inline duplication of the standard 3-step guard remains in scope commands

**Files:**
- No file changes — verification only

- [ ] **Step 1: Write failing tests (RED)**

  Add a final integration-style test to `test_preflight_consolidation.py`:

  ```python
  import subprocess, sys

  def test_lint_clean():
      result = subprocess.run(["make", "lint"], capture_output=True, text=True,
                              cwd=Path(__file__).parents[2])
      assert result.returncode == 0, f"Lint failed:\n{result.stdout}\n{result.stderr}"
  ```

  Run: `make test-unit` — must PASS (lint was clean before this feature; if it fails, fix lint issues first)

- [ ] **Step 2: Implement (GREEN)**

  Run full suite:
  ```
  make test-ci
  ```
  Expected: all tests pass, coverage gate met.

  If any failures: trace to specific command edit and fix in that command's file.

  Run: `make test-ci` — must PASS

- [ ] **Step 3: Refactor**
  Spot-check: open `commands/spec.md`, `plan.md`, `fix.md`, `backlog.md`, `resync.md`, `implement.md` — each `## ตรวจสอบก่อนเริ่ม` should have the reference line and no inline `Check \`zie-framework/\` exists` duplication.
  Run: `make test-ci` — still PASS
