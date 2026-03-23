---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-safety-check-redos-test.md
spec: specs/2026-03-24-audit-safety-check-redos-test-design.md
---

# Safety Check — Performance Contract Test for Very Long Commands (ReDoS Surface) — Implementation Plan

**Goal:** Add a `TestSafetyCheckPerformance` class to `test_hooks_safety_check.py` with 5 tests that assert the hook completes within a 2-second wall-clock bound for very long or adversarially crafted commands, documenting the performance contract and guarding against future ReDoS regressions.
**Architecture:** Each test uses `time.time()` around a `subprocess.run(..., timeout=10)` call to measure wall-clock elapsed. The 10-second hard kill prevents the suite from hanging if a future pattern causes catastrophic backtracking; the 2-second soft assertion is the documented contract. All current BLOCKS patterns use `\s+` with no nested quantifiers, so these tests are a regression guard rather than a known-failing scenario.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `tests/unit/test_hooks_safety_check.py` | Add class `TestSafetyCheckPerformance` with 5 test methods |
| Read-only | `hooks/safety-check.py` | Reference for BLOCKS/WARNS patterns — no changes |

---

## Task 1: Add TestSafetyCheckPerformance to test_hooks_safety_check.py

**Acceptance Criteria:**
- `test_very_long_safe_command_completes_quickly`: 100k-char safe command, `returncode == 0`, elapsed < 2.0s
- `test_very_long_blocked_prefix_completes_quickly`: blocked prefix + 100k noise, `returncode == 2`, `"BLOCKED" in stdout`, elapsed < 2.0s
- `test_adversarial_rm_rf_pattern_completes_quickly`: `rm -rf` + 50k spaces + `/`, completes < 2.0s (result may be blocked or not — document it)
- `test_adversarial_drop_database_pattern_completes_quickly`: `drop` + 50k spaces + `database mydb`, completes < 2.0s
- `test_empty_command_completes_quickly`: empty string, `returncode == 0`, elapsed < 0.5s

**Files:**
- Modify: `tests/unit/test_hooks_safety_check.py`

- [ ] **Step 1: Write failing tests (RED)**

  Append the new class. Tests are RED because the class does not yet exist:

  ```python
  import time  # add to existing imports at top of file

  class TestSafetyCheckPerformance:
      """Performance contract tests for safety-check.py.

      These tests assert that the hook completes within a wall-clock bound for
      very long or adversarially crafted inputs. They guard against ReDoS
      regressions from future pattern changes.

      Threshold: 2.0 seconds (generous to avoid CI flakiness; catastrophic
      backtracking takes orders of magnitude longer).
      """

      def test_very_long_safe_command_completes_quickly(self):
          start = time.time()
          r = run_hook("Bash", "git status " + "a" * 100_000)
          elapsed = time.time() - start
          assert r.returncode == 0
          assert elapsed < 2.0, f"Hook took {elapsed:.2f}s — possible ReDoS"

      def test_very_long_blocked_prefix_completes_quickly(self):
          start = time.time()
          r = run_hook("Bash", "rm -rf / " + "x" * 100_000)
          elapsed = time.time() - start
          assert r.returncode == 2
          assert "BLOCKED" in r.stdout
          assert elapsed < 2.0, f"Hook took {elapsed:.2f}s — possible ReDoS"

      def test_adversarial_rm_rf_pattern_completes_quickly(self):
          # Tests \s+ quantifier in rm -rf pattern with large whitespace between rm -rf and /
          cmd = "rm -rf " + " " * 50_000 + "/"
          start = time.time()
          r = run_hook("Bash", cmd)
          elapsed = time.time() - start
          # Result depends on whether pattern matches across large whitespace — document it
          assert elapsed < 2.0, f"Hook took {elapsed:.2f}s — possible ReDoS in rm -rf pattern"
          assert r.returncode in (0, 2), f"Unexpected returncode: {r.returncode}"

      def test_adversarial_drop_database_pattern_completes_quickly(self):
          # Tests \s+ in \bdrop\s+database\b with 50k spaces between keywords
          cmd = "drop" + " " * 50_000 + "database mydb"
          start = time.time()
          r = run_hook("Bash", cmd)
          elapsed = time.time() - start
          assert elapsed < 2.0, f"Hook took {elapsed:.2f}s — possible ReDoS in drop database pattern"
          assert r.returncode in (0, 2)

      def test_empty_command_completes_quickly(self):
          # Empty command exits at line 17 of safety-check.py — faster bound applies
          start = time.time()
          r = run_hook("Bash", "")
          elapsed = time.time() - start
          assert r.returncode == 0
          assert elapsed < 0.5, f"Hook took {elapsed:.2f}s on empty command"
  ```

  Run: `make test-unit` — must FAIL (class not yet present in file)

- [ ] **Step 2: Implement (GREEN)**

  Adding the class above to `test_hooks_safety_check.py` IS the implementation. Also add `import time` to the existing imports at the top of the file.

  The `run_hook` helper already exists in the file and accepts `(tool_name, command)` — it uses `subprocess.run` without a timeout. For the performance tests the hard-kill timeout must be added. Two options:

  Option A — Add a `run_hook_timed` helper used only by performance tests (preferred — avoids changing the shared `run_hook` signature):

  ```python
  def run_hook_timed(tool_name, command, timeout=10):
      """Like run_hook but with a hard subprocess timeout for performance tests."""
      hook = os.path.join(REPO_ROOT, "hooks", "safety-check.py")
      event = {"tool_name": tool_name, "tool_input": {"command": command}}
      return subprocess.run(
          [sys.executable, hook],
          input=json.dumps(event),
          capture_output=True,
          text=True,
          timeout=timeout,
      )
  ```

  Then replace `run_hook(...)` with `run_hook_timed(...)` in all five `TestSafetyCheckPerformance` methods.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  For `test_adversarial_rm_rf_pattern_completes_quickly` and `test_adversarial_drop_database_pattern_completes_quickly`, add an inline comment documenting the observed `returncode` result (0 or 2) after the first passing run — this makes the contract explicit for future readers:

  ```python
  # Observed result: returncode == 2 (rm -rf pattern matches even with large whitespace)
  # OR
  # Observed result: returncode == 0 (50k spaces exceeds \s+ match window — not blocked)
  ```

  Run: `make test-unit` — still PASS
