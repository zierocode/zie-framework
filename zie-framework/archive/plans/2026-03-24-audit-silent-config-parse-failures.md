---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-silent-config-parse-failures.md
spec: specs/2026-03-24-audit-silent-config-parse-failures-design.md
---

# Warn on Silent Config Parse Failures — Implementation Plan

**Goal:** Replace bare `except Exception: pass` config-load blocks in `auto-test.py` and `session-resume.py` with `except Exception as e: print(f"[zie] warning: ...", file=sys.stderr)` so corrupt `.config` files produce a visible warning.
**Architecture:** Two one-line changes, one in each hook. No helper is extracted. The warning goes to stderr so it appears in Claude's hook output without blocking execution. Config fallback to `{}` is unchanged.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/auto-test.py` | Add `as e` + stderr print to config-load except clause (line 73) |
| Modify | `hooks/session-resume.py` | Add `as e` + stderr print to config-load except clause (line 28) |
| Modify | `tests/unit/test_hooks_auto_test.py` | Add test for corrupt config warning |
| Modify | `tests/unit/test_hooks_session_resume.py` | Add test for corrupt config warning |

## Task 1: Warn on corrupt `.config` in `auto-test.py`

<!-- depends_on: none -->

**Acceptance Criteria:**
- When `.config` contains invalid JSON, `auto-test.py` prints a `[zie] warning:` message to stderr
- The hook still exits 0 and does not crash
- The warning message contains the exception text
- When `.config` is valid JSON, no warning is printed

**Files:**
- Modify: `hooks/auto-test.py`
- Modify: `tests/unit/test_hooks_auto_test.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_hooks_auto_test.py — add new class at end of file

  class TestAutoTestConfigParseWarning:
      def test_warns_on_corrupt_config(self, tmp_path):
          """Corrupt .config must produce a [zie] warning on stderr."""
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          (zf / ".config").write_text("this is not json {{{")
          r = run_hook(
              {"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}},
              tmp_cwd=tmp_path,
          )
          assert r.returncode == 0
          assert "[zie] warning" in r.stderr, (
              f"Expected '[zie] warning' in stderr, got: {r.stderr!r}"
          )

      def test_no_warning_on_valid_config(self, tmp_path):
          """Valid .config must not produce any warning."""
          cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
          r = run_hook(
              {"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}},
              tmp_cwd=cwd,
          )
          assert "[zie] warning" not in r.stderr

      def test_no_warning_when_config_missing(self, tmp_path):
          """Missing .config must not produce any warning (guarded by exists() check)."""
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          r = run_hook(
              {"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}},
              tmp_cwd=tmp_path,
          )
          assert "[zie] warning" not in r.stderr
  ```
  Run: `make test-unit` — must FAIL (currently bare `pass` produces no stderr output)

- [ ] **Step 2: Implement (GREEN)**
  ```python
  # hooks/auto-test.py — replace lines 71-74 config-load block

  # OLD:
  #     try:
  #         config = json.loads(config_file.read_text())
  #     except Exception:
  #         pass

  # NEW:
      try:
          config = json.loads(config_file.read_text())
      except Exception as e:
          print(f"[zie] warning: .config unreadable ({e}), using defaults", file=sys.stderr)
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Verify the existing `TestAutoTestGuardrails` tests still pass (valid-config path unchanged).
  Run: `make test-unit` — still PASS

## Task 2: Warn on corrupt `.config` in `session-resume.py`

<!-- depends_on: none -->

**Acceptance Criteria:**
- When `.config` contains invalid JSON, `session-resume.py` prints a `[zie] warning:` message to stderr
- The hook still exits 0 and prints its normal status output (using empty config defaults)
- No warning when `.config` is valid or missing

**Files:**
- Modify: `hooks/session-resume.py`
- Modify: `tests/unit/test_hooks_session_resume.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_hooks_session_resume.py — add new class at end of file

  class TestSessionResumeConfigParseWarning:
      def test_warns_on_corrupt_config(self, tmp_path):
          """Corrupt .config must produce a [zie] warning on stderr."""
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          (zf / ".config").write_text("not valid json !!!")
          r = run_hook(tmp_cwd=tmp_path)
          assert r.returncode == 0
          assert "[zie] warning" in r.stderr, (
              f"Expected '[zie] warning' in stderr, got: {r.stderr!r}"
          )

      def test_still_prints_output_with_corrupt_config(self, tmp_path):
          """Hook must still produce normal output even with corrupt config."""
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          (zf / ".config").write_text("{bad json")
          r = run_hook(tmp_cwd=tmp_path)
          assert r.returncode == 0
          assert "[zie-framework]" in r.stdout

      def test_no_warning_on_valid_config(self, tmp_path):
          """Valid .config must not produce any warning."""
          cwd = make_cwd(tmp_path, config={"project_type": "python-lib"})
          r = run_hook(tmp_cwd=cwd)
          assert "[zie] warning" not in r.stderr

      def test_no_warning_when_config_missing(self, tmp_path):
          """Missing .config (no file at all) must not produce any warning."""
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          r = run_hook(tmp_cwd=tmp_path)
          assert "[zie] warning" not in r.stderr
  ```
  Run: `make test-unit` — must FAIL (currently bare `pass` produces no stderr)

- [ ] **Step 2: Implement (GREEN)**
  ```python
  # hooks/session-resume.py — replace lines 25-29 config-load block

  # OLD:
  #     try:
  #         config = json.loads(config_file.read_text())
  #     except Exception:
  #         pass

  # NEW:
      try:
          config = json.loads(config_file.read_text())
      except Exception as e:
          print(f"[zie] warning: .config unreadable ({e}), using defaults", file=sys.stderr)
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Verify all existing `TestSessionResume*` tests still pass.
  Run: `make test-unit` — still PASS

---
*Commit: `git add hooks/auto-test.py hooks/session-resume.py tests/unit/test_hooks_auto_test.py tests/unit/test_hooks_session_resume.py && git commit -m "fix: warn on corrupt .config in auto-test and session-resume"`*
