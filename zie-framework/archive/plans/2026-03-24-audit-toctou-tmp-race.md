---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-toctou-tmp-race.md
spec: specs/2026-03-24-audit-toctou-tmp-race-design.md
---

# TOCTOU Race on /tmp Debounce File — Implementation Plan

**Goal:** Replace the non-atomic `debounce_file.write_text()` call in `auto-test.py` with an atomic write-then-rename so the check-then-write gap cannot be raced.
**Architecture:** Write debounce content to a `.tmp` sibling file first, then call `os.replace()` (POSIX-atomic rename) to move it into the final position. The existence/mtime read that precedes the write is already read-only and unchanged. Error handling wraps the atomic write in `try/except OSError` so a full `/tmp` does not crash the hook.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/auto-test.py` | Replace `debounce_file.write_text()` with atomic write-rename |
| Modify | `tests/unit/test_hooks_auto_test.py` | Assert atomic tmp sibling path is used; normal-write path still works |

---

## Task 1: Atomic Debounce Write

**Acceptance Criteria:**
- After a cache miss, the debounce file is written via a `.tmp` sibling rename, not direct `write_text`
- A full `/tmp` (OSError on write) does not crash the hook — it exits 0 silently
- All existing debounce tests remain green

**Files:**
- Modify: `hooks/auto-test.py`
- Modify: `tests/unit/test_hooks_auto_test.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to tests/unit/test_hooks_auto_test.py
  import os
  from unittest import mock

  class TestAutoTestAtomicDebounceWrite:
      """Debounce write must be atomic (write-then-rename, not direct write_text)."""

      @pytest.fixture(autouse=True)
      def _cleanup(self, tmp_path):
          yield
          for suffix in ("", ".tmp"):
              p = project_tmp_path("last-test" + suffix, tmp_path.name)
              if p.exists():
                  p.unlink()

      def test_debounce_write_uses_os_replace(self, tmp_path):
          """os.replace must be called during a cold-cache debounce write."""
          cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
          # Cold cache — no debounce file exists
          debounce = project_tmp_path("last-test", cwd.name)
          assert not debounce.exists()

          calls = []
          original_replace = os.replace

          def recording_replace(src, dst):
              calls.append((str(src), str(dst)))
              return original_replace(src, dst)

          with mock.patch("os.replace", side_effect=recording_replace):
              run_hook(
                  {"tool_name": "Edit", "tool_input": {"file_path": str(cwd / "hooks" / "utils.py")}},
                  tmp_cwd=cwd,
              )

          # os.replace must have been called with a .tmp src and the debounce dst
          assert any(
              src.endswith(".tmp") and dst == str(debounce)
              for src, dst in calls
          ), f"Expected atomic rename to {debounce}, got calls: {calls}"

      def test_debounce_write_oserror_does_not_crash_hook(self, tmp_path):
          """If /tmp write raises OSError, hook must exit 0 (no crash)."""
          cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
          debounce = project_tmp_path("last-test", cwd.name)
          assert not debounce.exists()

          with mock.patch("os.replace", side_effect=OSError("disk full")):
              r = run_hook(
                  {"tool_name": "Edit", "tool_input": {"file_path": str(cwd / "hooks" / "utils.py")}},
                  tmp_cwd=cwd,
              )

          assert r.returncode == 0
          assert "Traceback" not in r.stderr
  ```

  Run: `make test-unit` — must FAIL (`test_debounce_write_uses_os_replace` fails because `os.replace` is not called; `test_debounce_write_oserror_does_not_crash_hook` fails because the hook crashes on the mock OSError)

---

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # In hooks/auto-test.py, replace line 87:
  # BEFORE:
  debounce_file.write_text(file_path)

  # AFTER:
  try:
      tmp_write = debounce_file.parent / (debounce_file.name + ".tmp")
      tmp_write.write_text(file_path)
      os.replace(tmp_write, debounce_file)
  except OSError:
      pass  # /tmp full or unavailable — skip debounce, tests will run
  ```

  Also add `import os` to the top of the file if not already present.
  (It is already present on line 5 — no change needed there.)

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  No further structural changes. The `.tmp` sibling name (`debounce_file.name + ".tmp"`)
  is intentionally inline — no helper needed per YAGNI. The `except OSError: pass`
  pattern matches the existing `except Exception: pass` style in the hook.

  Run: `make test-unit` — still PASS

---

**Commit:** `git add hooks/auto-test.py tests/unit/test_hooks_auto_test.py && git commit -m "fix: audit-toctou-tmp-race — atomic write-then-rename for debounce file"`
