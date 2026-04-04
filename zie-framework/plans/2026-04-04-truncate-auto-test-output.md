---
approved: false
approved_at:
backlog: backlog/truncate-auto-test-output.md
---

# Truncate Auto-Test Output — Implementation Plan

**Goal:** Reduce pytest output noise in auto-test.py by truncating failure output to summary + first failure block, and skipping non-code file types entirely.
**Architecture:** Add `truncate_test_output(raw: str) -> str` helper inside `hooks/auto-test.py` and an extension skip-list guard before debounce. Both Popen and subprocess.run output paths use the same truncation helper. Unit tests added to the existing test file.
**Tech Stack:** Python 3.x, pytest, existing hooks/auto-test.py + tests/unit/test_hooks_auto_test.py.

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/auto-test.py` | Add `truncate_test_output()`, add extension skip guard, apply truncation to both output paths |
| Modify | `tests/unit/test_hooks_auto_test.py` | Add unit tests for `truncate_test_output()` and the extension skip guard |

---

## Acceptance Criteria

| ID | Criterion |
| --- | --- |
| AC-1 | Editing a `.md` file → hook exits 0 silently (no additionalContext, no debounce write) |
| AC-2 | `.json`, `.yaml`, `.yml`, `.toml`, `.cfg`, `.ini`, `.txt` files also skipped silently |
| AC-3 | `.MD`, `.JSON` (uppercase extensions) skipped via `.lower()` normalisation |
| AC-4 | File with no extension (e.g. `Makefile`) proceeds normally — not skipped |
| AC-5 | `truncate_test_output()` returns summary line + first FAILED block, capped at 30 lines total |
| AC-6 | `truncate_test_output()` falls back to first 10 non-empty lines when no FAILED block found |
| AC-7 | On zero exit (tests pass), existing `Tests pass ✓` message emitted unchanged |
| AC-8 | Both Popen path and subprocess.run path use `truncate_test_output()` on non-zero exit |
| AC-9 | `make test-ci` exits 0 |

---

## Tasks

### Task 1: Write failing tests for `truncate_test_output()` (RED)

**Files:**
- Modify: `tests/unit/test_hooks_auto_test.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add `TestTruncateTestOutput` class at the end of the test file:

  ```python
  import importlib.util, types

  def _load_truncate():
      """Import truncate_test_output from auto-test.py via importlib."""
      import importlib.util, sys
      spec = importlib.util.spec_from_file_location(
          "auto_test_hook",
          os.path.join(HOOKS_DIR, "auto-test.py"),
      )
      mod = importlib.util.module_from_spec(spec)
      # Prevent __main__ block from running
      mod.__name__ = "auto_test_hook"
      try:
          spec.loader.exec_module(mod)
      except SystemExit:
          pass
      return mod.truncate_test_output


  class TestTruncateTestOutput:
      def setup_method(self):
          self.fn = _load_truncate()

      def test_summary_line_extracted(self):
          """AC-5: summary line present in output."""
          raw = (
              "collected 5 items\n\ntest_foo.py::test_bar FAILED\n\n"
              "FAILED test_foo.py::test_bar - AssertionError\n\n"
              "1 failed, 4 passed in 0.12s\n"
          )
          result = self.fn(raw)
          assert "1 failed, 4 passed" in result

      def test_first_failed_block_extracted(self):
          """AC-5: first FAILED block present."""
          raw = (
              "FAILED test_foo.py::test_bar - AssertionError: expected 1\n"
              "E   assert 0 == 1\n\n"
              "2 failed in 0.5s\n"
          )
          result = self.fn(raw)
          assert "FAILED test_foo.py::test_bar" in result
          assert "assert 0 == 1" in result

      def test_capped_at_30_lines(self):
          """AC-5: output capped at 30 lines."""
          long_block = "\n".join([f"E   line {i}" for i in range(100)])
          raw = f"FAILED test_x.py::test_y\n{long_block}\n\n1 failed in 1s\n"
          result = self.fn(raw)
          assert len(result.splitlines()) <= 30

      def test_fallback_when_no_failed_block(self):
          """AC-6: fallback to first 10 non-empty lines."""
          raw = "\n".join([f"line {i}" for i in range(50)]) + "\n1 failed in 0.1s\n"
          result = self.fn(raw)
          non_empty = [l for l in result.splitlines() if l.strip()]
          # at most 10 content lines (summary + fallback lines)
          assert len(non_empty) <= 12  # header + summary + up to 10

      def test_header_present(self):
          """Output starts with zie-framework header."""
          raw = "FAILED test.py::t\n\n1 failed in 0.1s\n"
          result = self.fn(raw)
          assert "[zie-framework] Tests FAILED" in result
  ```

  Run: `make test-unit` — must FAIL (function doesn't exist yet)

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/auto-test.py`, add `truncate_test_output` function after imports, before `find_matching_test`:

  ```python
  import re as _re

  _SUMMARY_RE = _re.compile(r'\d+\s+(passed|failed|error|skipped|xfailed|xpassed)')

  def truncate_test_output(raw: str) -> str:
      """Reduce pytest output to summary line + first FAILED block, capped at 30 lines."""
      lines = raw.splitlines()

      # Find summary line (last matching line)
      summary_line = ""
      for line in reversed(lines):
          if _SUMMARY_RE.search(line):
              summary_line = line.strip()
              break

      # Find first FAILED block
      failed_block: list[str] = []
      in_block = False
      for line in lines:
          if not in_block and _re.match(r'^(FAILED|E   |_ )', line):
              in_block = True
          if in_block:
              if not line.strip() or line.startswith('='):
                  break
              failed_block.append(line)

      header = "[zie-framework] Tests FAILED — fix before continuing"

      if failed_block:
          parts = [header]
          if summary_line:
              parts.append(summary_line)
          parts.append("")
          parts.extend(failed_block)
          result = "\n".join(parts)
          # Cap at 30 lines
          result_lines = result.splitlines()
          if len(result_lines) > 30:
              result = "\n".join(result_lines[:30])
          return result
      else:
          # Fallback: first 10 non-empty lines
          non_empty = [l for l in lines if l.strip()][:10]
          parts = [header]
          if summary_line:
              parts.append(summary_line)
          parts.append("")
          parts.extend(non_empty)
          return "\n".join(parts)
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify the regex import (`_re`) doesn't clash with existing imports. If `re` is already imported, use it directly rather than aliasing. Clean up any dead comments.

  Run: `make test-unit` — still PASS

---

### Task 2: Write failing tests for extension skip guard (RED)

<!-- depends_on: Task 1 -->

**Files:**
- Modify: `tests/unit/test_hooks_auto_test.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add `TestExtensionSkipGuard` class:

  ```python
  class TestExtensionSkipGuard:
      """AC-1, AC-2, AC-3, AC-4: extension skip guard fires before debounce."""

      def test_md_file_skipped_silently(self, tmp_path):
          """AC-1: .md file → no output, exit 0."""
          cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
          md_file = cwd / "README.md"
          md_file.write_text("# test")
          r = run_hook(
              {"tool_name": "Edit", "tool_input": {"file_path": str(md_file)}},
              tmp_cwd=cwd,
          )
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      @pytest.mark.parametrize("ext", [".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".txt"])
      def test_non_code_extensions_skipped(self, tmp_path, ext):
          """AC-2: other non-code extensions also skipped."""
          cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
          f = cwd / f"config{ext}"
          f.write_text("data")
          r = run_hook(
              {"tool_name": "Edit", "tool_input": {"file_path": str(f)}},
              tmp_cwd=cwd,
          )
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_uppercase_extension_skipped(self, tmp_path):
          """AC-3: .MD uppercase skipped via .lower()."""
          cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
          f = cwd / "README.MD"
          f.write_text("# test")
          r = run_hook(
              {"tool_name": "Edit", "tool_input": {"file_path": str(f)}},
              tmp_cwd=cwd,
          )
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_no_extension_proceeds(self, tmp_path):
          """AC-4: file with no extension (Makefile) not skipped — hook proceeds to additionalContext."""
          cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
          f = cwd / "Makefile"
          f.write_text("all:\n\techo hi")
          r = run_hook(
              {"tool_name": "Edit", "tool_input": {"file_path": str(f)}},
              tmp_cwd=cwd,
          )
          # Hook proceeds past the skip guard — additionalContext JSON should be printed
          assert r.returncode == 0
          assert "additionalContext" in r.stdout

      def test_skip_guard_before_debounce(self, tmp_path):
          """AC-1 variant: skipped file does not write debounce sentinel."""
          cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
          md_file = cwd / "notes.md"
          md_file.write_text("hi")
          run_hook(
              {"tool_name": "Edit", "tool_input": {"file_path": str(md_file)}},
              tmp_cwd=cwd,
          )
          debounce = project_tmp_path("last-test", cwd.name)
          assert not debounce.exists()
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/auto-test.py`, add the extension skip guard after `changed = Path(file_path).resolve()` and before `cwd_resolved` check:

  ```python
  _SKIP_EXTENSIONS = {".md", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".txt"}
  if changed.suffix.lower() in _SKIP_EXTENSIONS:
      sys.exit(0)
  ```

  The guard must appear before the `additionalContext` injection line and before any debounce write.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Confirm `_SKIP_EXTENSIONS` is defined as a module-level constant or inline set — either works; inline set is fine for readability. No other changes needed.

  Run: `make test-unit` — still PASS

---

### Task 3: Apply `truncate_test_output()` to both output paths (GREEN wire-up)

<!-- depends_on: Task 1, Task 2 -->

**Files:**
- Modify: `hooks/auto-test.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add integration-style test in `TestTruncateTestOutput` (or a new class) that exercises the hook end-to-end with a real failing test to confirm truncation is applied:

  ```python
  class TestAutoTestTruncation:
      """AC-7, AC-8: truncation applied on non-zero exit, pass path unchanged."""

      def test_pass_path_unchanged(self, tmp_path):
          """AC-7: on zero exit, 'Tests pass ✓' is printed."""
          cwd = make_cwd(tmp_path, config={
              "test_runner": "pytest",
              "auto_test_max_wait_s": 0,
              "auto_test_timeout_ms": 10000,
          })
          # Create a trivial passing test
          tests_dir = cwd / "tests"
          tests_dir.mkdir()
          (tests_dir / "test_pass.py").write_text("def test_ok(): assert True\n")
          py_file = cwd / "mymod.py"
          py_file.write_text("x = 1\n")
          r = run_hook(
              {"tool_name": "Edit", "tool_input": {"file_path": str(py_file)}},
              tmp_cwd=cwd,
          )
          assert "Tests pass ✓" in r.stdout

      def test_fail_path_truncated(self, tmp_path):
          """AC-8: on non-zero exit, truncated output via truncate_test_output()."""
          cwd = make_cwd(tmp_path, config={
              "test_runner": "pytest",
              "auto_test_max_wait_s": 0,
              "auto_test_timeout_ms": 10000,
          })
          tests_dir = cwd / "tests"
          tests_dir.mkdir()
          # Write a failing test with lots of output
          (tests_dir / "test_fail.py").write_text(
              "def test_bad():\n"
              "    msg = 'x' * 500\n"
              "    assert False, msg\n"
          )
          py_file = cwd / "mymod.py"
          py_file.write_text("x = 1\n")
          r = run_hook(
              {"tool_name": "Edit", "tool_input": {"file_path": str(py_file)}},
              tmp_cwd=cwd,
          )
          assert "[zie-framework] Tests FAILED" in r.stdout
          # Truncated — should not contain more than 35 non-empty lines of output
          lines = [l for l in r.stdout.splitlines() if l.strip()]
          assert len(lines) <= 35
  ```

  Run: `make test-unit` — tests may partially fail (truncation not yet wired to both paths)

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/auto-test.py`, replace the existing failure output blocks in both paths:

  Popen path (replace lines printing `lines[:20]`):
  ```python
  if rc == 0:
      print("[zie-framework] Tests pass ✓")
  else:
      print(truncate_test_output(stdout_data + stderr_data))
  ```

  subprocess.run path (replace lines printing `lines[:20]`):
  ```python
  if result.returncode == 0:
      print("[zie-framework] Tests pass ✓")
  else:
      print(truncate_test_output(result.stdout + result.stderr))
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Remove the now-dead `lines = (stdout_data + stderr_data).splitlines()` and `for line in lines[:20]` patterns from both paths. Clean up any leftover intermediate variables.

  Run: `make test-unit` — still PASS
  Run: `make lint` — exit 0

---

## Final Gate

Run: `make test-ci` — must exit 0 (AC-9)
