---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-implement-agent-mode-check.md
---

# Lean implement Agent-Mode Check — Implementation Plan

**Goal:** Replace the blocking yes/no gate in `/implement` Step 0 with a single non-blocking advisory tip so that every invocation continues immediately without user input.
**Architecture:** Pure markdown edit to `commands/implement.md` — no Python, no hooks, no config changes. The test file `test_command_zie_implement_agent_warn.py` is updated to assert the new advisory-only pattern instead of the old blocking pattern.
**Tech Stack:** Markdown (commands), pytest (tests)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/implement.md` | Replace Step 0 blocking prompt with advisory tip |
| Modify | `tests/unit/test_command_zie_implement_agent_warn.py` | Invert assertions to match advisory-only pattern |

---

## Task 1: Invert test assertions to advisory-only pattern

**Acceptance Criteria:**
- `test_interactive_confirmation_present` is removed
- `test_stop_on_no` is removed
- A new test `test_no_blocking_prompt` asserts `"Continue anyway?"` is NOT in `implement.md`
- A new test `test_advisory_tip_present` asserts `"Tip: for best results run inside"` IS in `implement.md`
- Existing `test_agent_mode_command_referenced` is retained unchanged
- `make test-unit` FAILS after this task (tests assert the new pattern but `implement.md` still has old text)

**Files:**
- Modify: `tests/unit/test_command_zie_implement_agent_warn.py`

- [ ] **Step 1: Write failing tests (RED)**

  Replace the file content with:

  ```python
  """Structural tests: /implement step 0 must print advisory tip only (non-blocking)."""
  import os
  from pathlib import Path

  REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
  IMPLEMENT_CMD = Path(REPO_ROOT) / "commands" / "implement.md"


  class TestAgentModeAdvisory:
      def _src(self):
          return IMPLEMENT_CMD.read_text()

      def test_no_blocking_prompt(self):
          """Step 0 must NOT ask for confirmation — advisory only, no interactive gate."""
          src = self._src()
          assert "Continue anyway?" not in src, (
              "implement.md step 0 must not contain an interactive confirmation prompt"
          )

      def test_advisory_tip_present(self):
          """Step 0 must print a non-blocking advisory tip."""
          src = self._src()
          assert "Tip: for best results run inside" in src, (
              "implement.md step 0 must contain the advisory tip text"
          )

      def test_agent_mode_command_referenced(self):
          """Advisory tip references the correct agent mode command."""
          src = self._src()
          assert "zie-implement-mode" in src, (
              "implement.md step 0 must mention the recommended agent mode"
          )
  ```

  Run: `make test-unit` — must FAIL (RED state). Both `test_no_blocking_prompt` and `test_advisory_tip_present` fail: the old `implement.md` still contains `"Continue anyway?"` (so the `not in` assertion fails) and still lacks the advisory tip text. This is the expected RED state — do not proceed until you see these two failures.

- [ ] **Step 2: Implement (GREEN)**

  No implementation in this task — implementation is in Task 2. This task only rewrites the tests. After Task 2 completes, all three tests will pass.

  Skip `make test-unit` here — tests intentionally fail until Task 2 is done.

- [ ] **Step 3: Refactor**

  No refactor needed. Module docstring is already updated in Step 1.

---

## Task 2: Replace Step 0 in implement.md with advisory tip

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `implement.md` Step 0 no longer contains `"Continue anyway?"`
- `implement.md` Step 0 no longer contains `"if no → STOP"`
- `implement.md` Step 0 contains exactly: `Tip: for best results run inside \`claude --agent zie-framework:zie-implement-mode\``
- `make test-unit` passes all three tests in `TestAgentModeAdvisory`

**Files:**
- Modify: `commands/implement.md`

- [ ] **Step 1: Write failing tests (RED)**

  Tests already written in Task 1 — no new tests needed here. Confirm current state:

  Run: `make test-unit -k test_command_zie_implement_agent_warn` — must FAIL (`test_advisory_tip_present` fails, `test_no_blocking_prompt` may fail)

- [ ] **Step 2: Implement (GREEN)**

  In `commands/implement.md`, replace the entire Step 0 block:

  **Find (lines ~17–20):**
  ```markdown
  0. **Pre-flight: Agent mode check** — if not running with `--agent zie-framework:zie-implement-mode`:
     print `⚠️ Running /implement outside agent session. permissionMode and tool preloading will be missing.`
     print `Recommended: exit and relaunch with: claude --agent zie-framework:zie-implement-mode`
     Ask: `Continue anyway? (yes / no)` — if no → STOP. If yes → continue.
  ```

  **Replace with:**
  ```markdown
  0. **Pre-flight: Agent mode check** — print advisory tip:
     `Tip: for best results run inside \`claude --agent zie-framework:zie-implement-mode\``
     Continue immediately — no user input required.
  ```

  Run: `make test-unit` — must PASS (all three tests in `TestAgentModeAdvisory`)

- [ ] **Step 3: Refactor**

  Verify the surrounding numbered list in `implement.md` is still correctly formatted (steps 0–8 sequential, no broken indentation). Read lines 15–25 of `commands/implement.md` to confirm.

  Run: `make test-unit` — still PASS

---
