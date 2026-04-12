---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-auto-test-context-before-debounce.md
---

# Lean auto-test additionalContext — Implementation Plan

**Goal:** Move `additionalContext` emission in `auto-test.py` to after the debounce check and test-file check, suppressing it (and the broad pytest fallback) when no matching test file exists.
**Architecture:** Single-file hook change — reorder two blocks in `hooks/auto-test.py`. The `additionalContext` JSON print moves from after `find_matching_test()` to after a new early-exit gate on `matching_test is None`. The broad `pytest tests/` fallback command branch is also removed, since the early exit replaces it.
**Tech Stack:** Python 3.x (hook), pytest (test suite)

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/auto-test.py` | Remove "no test file" context branch; add `sys.exit(0)` gate on `matching_test is None`; move `additionalContext` print to after gate |
| Modify | `tests/unit/test_hooks_auto_test.py` | Add tests verifying (a) no context when `matching_test is None`, (b) no broad pytest fallback run |

---

## Task 1: Gate on `matching_test is None` and move `additionalContext`

**Acceptance Criteria:**
- When `find_matching_test()` returns `None` (after debounce clears), hook exits 0 with no stdout — no `additionalContext` JSON, no test run.
- When `find_matching_test()` returns a path, `additionalContext` JSON is still printed before the test run.
- The broad `pytest tests/` fallback branch no longer exists in the source.

**Files:**
- Modify: `hooks/auto-test.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add to `tests/unit/test_hooks_auto_test.py` in a new class `TestAutoTestContextGate`:

  ```python
  class TestAutoTestContextGate:
      """additionalContext is only emitted when a matching test file is found."""

      @pytest.fixture(autouse=True)
      def _cleanup(self, tmp_path):
          yield
          p = project_tmp_path("last-test", tmp_path.name)
          if p.exists():
              p.unlink()

      def test_no_context_when_no_matching_test(self, tmp_path):
          """When no test file matches, hook must exit 0 with empty stdout."""
          cwd = make_cwd(tmp_path, config={"test_runner": "pytest", "auto_test_debounce_ms": 0})
          # Edit a file with no corresponding test file
          target = cwd / "some_unmatched_module.py"
          target.write_text("x = 1")
          r = run_hook(
              {"tool_name": "Edit", "tool_input": {"file_path": str(target)}},
              tmp_cwd=cwd,
          )
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_no_fallback_pytest_tests_dir_run(self, tmp_path):
          """Broad pytest tests/ fallback must not run when matching_test is None."""
          cwd = make_cwd(tmp_path, config={"test_runner": "pytest", "auto_test_debounce_ms": 0})
          target = cwd / "orphan_module.py"
          target.write_text("x = 1")
          r = run_hook(
              {"tool_name": "Edit", "tool_input": {"file_path": str(target)}},
              tmp_cwd=cwd,
          )
          # No test run output — neither pass nor fail banner
          assert "[zie-framework] Tests" not in r.stdout

      def test_context_emitted_when_matching_test_found(self, tmp_path):
          """additionalContext must be printed when a matching test file exists."""
          cwd = make_cwd(tmp_path, config={"test_runner": "pytest", "auto_test_debounce_ms": 0})
          tests_dir = cwd / "tests"
          tests_dir.mkdir()
          test_file = tests_dir / "test_payments.py"
          test_file.write_text("def test_stub(): pass")
          target = cwd / "payments.py"
          target.write_text("x = 1")
          r = run_hook(
              {"tool_name": "Edit", "tool_input": {"file_path": str(target)}},
              tmp_cwd=cwd,
          )
          assert "additionalContext" in r.stdout
          assert "payments" in r.stdout
  ```

  Run: `make test-unit` — tests must **FAIL** (current hook still emits "No test file found..." context and runs `pytest tests/`)

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/auto-test.py`, replace the block at lines 162–182 (the `find_matching_test` call through the pytest command builder's else-branch):

  **Remove** (old block):
  ```python
      # Single find_matching_test call — result reused for context injection and test command
      matching_test = find_matching_test(changed, test_runner, cwd)

      # additionalContext injection — only fires when tests will actually run (after debounce)
      if matching_test:
          _additional_context = f"Affected test: {matching_test}"
      else:
          _additional_context = f"No test file found for {changed.name} — write one"
      print(json.dumps({"additionalContext": _additional_context}))

      auto_test_timeout_ms = config["auto_test_timeout_ms"]
      auto_test_max_wait_s = config["auto_test_max_wait_s"]
      timeout = auto_test_timeout_ms // 1000

      # Build test command
      if test_runner == "pytest":
          if matching_test:
              cmd = ["python3", "-m", "pytest", matching_test, "-x", "-q", "--tb=short", "--no-header"]
          else:
              cmd = ["python3", "-m", "pytest", "tests/", "-x", "-q", "--tb=short", "--no-header",
                     "-m", "not integration"]
  ```

  **Replace with** (new block):
  ```python
      # Single find_matching_test call — result reused for context injection and test command
      matching_test = find_matching_test(changed, test_runner, cwd)

      # Gate: no matching test file → suppress context and skip test run entirely
      if matching_test is None:
          sys.exit(0)

      # additionalContext — only emitted when a matching test exists and debounce cleared
      print(json.dumps({"additionalContext": f"Affected test: {matching_test}"}))

      auto_test_timeout_ms = config["auto_test_timeout_ms"]
      auto_test_max_wait_s = config["auto_test_max_wait_s"]
      timeout = auto_test_timeout_ms // 1000

      # Build test command
      if test_runner == "pytest":
          cmd = ["python3", "-m", "pytest", matching_test, "-x", "-q", "--tb=short", "--no-header"]
  ```

  Run: `make test-unit` — must **PASS**

- [ ] **Step 3: Refactor**

  - Verify no dead `else` branch remains for pytest (the `if matching_test:` inside the command builder is now gone — `matching_test` is guaranteed non-None at this point).
  - Confirm the comment on line 162 still reads accurately: "result reused for context injection and test command".
  - Run: `make test-unit` — still **PASS**
  - Run: `make lint` — no violations

---

## Summary

This is a **S-plan** (1 task, 2 files). The change is a pure reordering + gate addition:

1. `find_matching_test()` is called as before.
2. A new `if matching_test is None: sys.exit(0)` gate replaces both the "no test file" context string and the broad `pytest tests/` fallback.
3. `additionalContext` is printed only for the matched-test path.

No changes to `find_matching_test()`, debounce logic, vitest/jest paths, or config loading.
