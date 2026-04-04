---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-prompt-pass-through.md
---

# Lean Prompt Pass-Through — Implementation Plan

**Goal:** Suppress intent-sdlc SDLC state injection for all slash-command messages by extending the outer guard early-exit to any message starting with `/`.
**Architecture:** Single-line change to `hooks/intent-sdlc.py` outer guard block — replaces the compound `startswith("/") and len < 20` condition with `startswith("/")` alone, moving the check before any I/O. Tests added to `tests/unit/test_intent_sdlc_early_exit.py`.
**Tech Stack:** Python 3.x, pytest, subprocess hook test pattern.

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/intent-sdlc.py` | Extend slash-command early-exit in outer guard |
| Modify | `tests/unit/test_intent_sdlc_early_exit.py` | Add slash-command early-exit test cases |

---

## Task 1: Extend slash-command early-exit in outer guard

**Acceptance Criteria:**
- A message starting with `/` followed by any text (including args) exits the hook silently with no stdout
- The old `len(first_token) < 20` check is replaced by `startswith("/")`
- Messages that don't start with `/` continue to pass through unchanged

**Files:**
- Modify: `hooks/intent-sdlc.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add a new test class to `tests/unit/test_intent_sdlc_early_exit.py`:

  ```python
  class TestSlashCommandGate:
      """Gate: any message starting with '/' must exit silently — no SDLC injection."""

      def test_slash_command_with_args_exits(self, tmp_path):
          # /sprint slug1 slug2 --dry-run — previously NOT caught (len > 20)
          cwd = make_cwd_with_zf(tmp_path)
          r = run_hook("/sprint slug1 slug2 --dry-run", tmp_cwd=cwd, session_id="test-sc-sprint")
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_slash_command_long_name_exits(self, tmp_path):
          # /zie-framework:spec-design some-slug — len > 20, previously leaked
          cwd = make_cwd_with_zf(tmp_path)
          r = run_hook("/zie-framework:spec-design some-slug", tmp_cwd=cwd, session_id="test-sc-long")
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_slash_command_no_args_exits(self, tmp_path):
          # /implement — len=10, already caught before, still caught after change
          cwd = make_cwd_with_zf(tmp_path)
          r = run_hook("/implement", tmp_cwd=cwd, session_id="test-sc-impl")
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_non_slash_prefix_passes(self, tmp_path):
          # Does NOT start with '/' — must still produce output (has SDLC keyword)
          cwd = make_cwd_with_zf(tmp_path)
          r = run_hook("i want to implement this feature now", tmp_cwd=cwd, session_id="test-sc-no-slash")
          assert r.returncode == 0
          assert r.stdout.strip() != ""

      def test_mid_string_slash_passes(self, tmp_path):
          # Contains '/' mid-string — does NOT start with '/', must pass through
          cwd = make_cwd_with_zf(tmp_path)
          r = run_hook("please run /spec on the backlog item", tmp_cwd=cwd, session_id="test-sc-mid")
          assert r.returncode == 0
          assert r.stdout.strip() != ""
  ```

  Run: `make test-unit` — `TestSlashCommandGate::test_slash_command_with_args_exits` and `test_slash_command_long_name_exits` MUST FAIL (they currently leak output).

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/intent-sdlc.py`, locate the outer guard block (around line 234):

  **Before:**
  ```python
  if message.startswith("/") and len(message.split()[0]) < 20:
      sys.exit(0)
  ```

  **After:**
  ```python
  if message.startswith("/"):
      sys.exit(0)
  ```

  Run: `make test-unit` — ALL tests in `TestSlashCommandGate` MUST PASS.

- [ ] **Step 3: Refactor**

  No structural changes needed — the diff is a single condition simplification.
  Verify no other early-exit logic in the outer block was inadvertently affected.

  Run: `make test-unit` — still PASS, including all pre-existing `TestLengthGate` and `TestKeywordGate` cases.
