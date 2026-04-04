---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-counter-valueerror.md
spec: specs/2026-03-24-audit-counter-valueerror-design.md
---

# Guard wip-checkpoint Counter File Against ValueError on Corrupt Content — Implementation Plan

**Goal:** Add three tests to `TestWipCheckpointCounter` that verify the hook recovers gracefully (exits 0, writes counter `"1"`) when the counter file contains non-numeric, whitespace-only, or empty content.
**Architecture:** The hook already has a broad `except Exception` guard around the counter read at line 38-41 of `wip-checkpoint.py`. Tests verify this contract is upheld by pre-writing corrupt counter files and asserting the hook's output and the counter's final state. If the implementation turns out NOT to recover correctly, `wip-checkpoint.py` lines 38-41 are patched to use explicit `except (ValueError, OSError)` with `count = 0` reset.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `tests/unit/test_hooks_wip_checkpoint.py` | Add 3 test methods to `TestWipCheckpointCounter` |
| Modify (if needed) | `hooks/wip-checkpoint.py` | Tighten counter read guard if tests expose incorrect recovery |

---

## Task 1: Add corrupt counter file recovery tests to TestWipCheckpointCounter

**Acceptance Criteria:**
- `test_corrupt_counter_file_resets_gracefully`: pre-write `"not-a-number\n"`, run hook, assert `returncode == 0`, counter contains `"1"`, `r.stderr` contains `"wip-checkpoint"`
- `test_whitespace_only_counter_file_resets_gracefully`: pre-write `"   \n"`, same assertions
- `test_empty_counter_file_resets_gracefully`: pre-write `""`, assert `returncode == 0`, counter contains `"1"`
- All three tests are cleaned up by the existing `_cleanup_counter` autouse fixture

**Files:**
- Modify: `tests/unit/test_hooks_wip_checkpoint.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add the three tests to `TestWipCheckpointCounter`. They are RED because they do not yet exist:

  ```python
  def test_corrupt_counter_file_resets_gracefully(self, tmp_path):
      cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
      # Pre-write corrupt (non-numeric) content
      counter_path(tmp_path.name).write_text("not-a-number\n")
      r = run_hook(tmp_cwd=cwd, env_overrides={
          "ZIE_MEMORY_API_KEY": "fake-key",
          "ZIE_MEMORY_API_URL": "https://localhost:19999",
      })
      # RED: these assertions are not yet verified
      assert r.returncode == 0
      assert counter_path(tmp_path.name).read_text().strip() == "1"
      assert "wip-checkpoint" in r.stderr

  def test_whitespace_only_counter_file_resets_gracefully(self, tmp_path):
      cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
      # int("") raises ValueError — whitespace stripped to empty string
      counter_path(tmp_path.name).write_text("   \n")
      r = run_hook(tmp_cwd=cwd, env_overrides={
          "ZIE_MEMORY_API_KEY": "fake-key",
          "ZIE_MEMORY_API_URL": "https://localhost:19999",
      })
      assert r.returncode == 0
      assert counter_path(tmp_path.name).read_text().strip() == "1"
      assert "wip-checkpoint" in r.stderr

  def test_empty_counter_file_resets_gracefully(self, tmp_path):
      cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
      # int("") raises ValueError
      counter_path(tmp_path.name).write_text("")
      r = run_hook(tmp_cwd=cwd, env_overrides={
          "ZIE_MEMORY_API_KEY": "fake-key",
          "ZIE_MEMORY_API_URL": "https://localhost:19999",
      })
      assert r.returncode == 0
      assert counter_path(tmp_path.name).read_text().strip() == "1"
  ```

  Run: `make test-unit` — must FAIL (tests not collected yet, since they don't exist in the file)

- [ ] **Step 2: Implement (GREEN)**

  Adding the three test methods above to `TestWipCheckpointCounter` IS the implementation for this pure-test item. Run:

  Run: `make test-unit` — must PASS

  If `test_corrupt_counter_file_resets_gracefully` or `test_whitespace_only_counter_file_resets_gracefully` FAIL because `r.stderr` does not contain `"wip-checkpoint"`, it means the `except Exception` block is not catching `ValueError` from `int("   ".strip())`. In that case, patch `wip-checkpoint.py`:

  ```python
  # hooks/wip-checkpoint.py — lines 37-41, replace:
  # BEFORE:
  if counter_file.exists():
      try:
          count = int(counter_file.read_text().strip())
      except Exception as e:
          print(f"[zie-framework] wip-checkpoint: {e}", file=sys.stderr)

  # AFTER (more explicit, same net behaviour):
  if counter_file.exists():
      try:
          count = int(counter_file.read_text().strip())
      except (ValueError, OSError) as e:
          print(f"[zie-framework] wip-checkpoint: {e}", file=sys.stderr)
          count = 0  # explicit reset — count was already 0, but state is now clear
  ```

  Re-run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify `test_empty_counter_file_resets_gracefully` does NOT assert `r.stderr` — the empty string case produces `int("") → ValueError` which IS caught and printed, but whether stderr contains the message depends on implementation detail. Keep the assertion minimal (only `returncode` and counter value) for this case to avoid brittleness.

  If the implementation patch was applied, confirm the `except` clause change does not break `TestWipCheckpointGuardrails` or any other test class.

  Run: `make test-unit` — still PASS
