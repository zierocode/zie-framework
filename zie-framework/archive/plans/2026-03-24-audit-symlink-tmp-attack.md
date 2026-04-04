---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-symlink-tmp-attack.md
spec: specs/2026-03-24-audit-symlink-tmp-attack-design.md
---

# Symlink Attack on /tmp State Files — Implementation Plan

**Goal:** Prevent hooks from overwriting arbitrary files via pre-planted symlinks at `/tmp/zie-*` paths by adding a `safe_write_tmp()` helper that checks `os.path.islink()` before writing.
**Architecture:** New `safe_write_tmp(path: Path, content: str) -> bool` function in `hooks/utils.py`. It combines the symlink check with the atomic write-then-rename from the TOCTOU spec. `auto-test.py` and `wip-checkpoint.py` replace their direct `/tmp` writes with calls to this helper. The helper returns `bool` so callers can treat a blocked write as a cold cache.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/utils.py` | Add `safe_write_tmp(path, content) -> bool` |
| Modify | `hooks/auto-test.py` | Replace debounce `write_text` / atomic write with `safe_write_tmp()` |
| Modify | `hooks/wip-checkpoint.py` | Replace counter `write_text` with `safe_write_tmp()` |
| Modify | `tests/unit/test_utils.py` | Unit tests for `safe_write_tmp` |

---

## Task 1: `safe_write_tmp` helper in utils.py

**Acceptance Criteria:**
- Returns `False` and prints a stderr warning when target path is a symlink
- Returns `True` and writes content atomically when path is not a symlink
- Returns `False` (no crash) when an `OSError` is raised during write
- Works correctly when path does not yet exist (first-run)
- Symlink pointing to non-existent target is still blocked

**Files:**
- Modify: `hooks/utils.py`
- Modify: `tests/unit/test_utils.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to tests/unit/test_utils.py

  import os
  import sys

  # Add to existing imports at top of file (already has: from utils import parse_roadmap_now, project_tmp_path)
  # Update import line to also import safe_write_tmp:
  # from utils import parse_roadmap_now, project_tmp_path, safe_write_tmp

  class TestSafeWriteTmp:
      def test_normal_write_returns_true(self, tmp_path):
          from utils import safe_write_tmp
          target = tmp_path / "zie-test-foo"
          result = safe_write_tmp(target, "hello")
          assert result is True
          assert target.read_text() == "hello"

      def test_normal_write_is_atomic(self, tmp_path):
          """Content is written via a .tmp sibling then renamed."""
          from utils import safe_write_tmp
          target = tmp_path / "zie-test-atomic"
          safe_write_tmp(target, "data")
          tmp_sibling = tmp_path / "zie-test-atomic.tmp"
          # After success, sibling must not remain
          assert not tmp_sibling.exists()
          assert target.read_text() == "data"

      def test_symlink_returns_false(self, tmp_path):
          from utils import safe_write_tmp
          real_file = tmp_path / "real.txt"
          real_file.write_text("secret")
          link = tmp_path / "zie-test-link"
          link.symlink_to(real_file)
          result = safe_write_tmp(link, "overwrite")
          assert result is False
          # Original file must be untouched
          assert real_file.read_text() == "secret"

      def test_symlink_to_nonexistent_returns_false(self, tmp_path):
          from utils import safe_write_tmp
          link = tmp_path / "zie-test-dangling"
          link.symlink_to(tmp_path / "does-not-exist")
          result = safe_write_tmp(link, "data")
          assert result is False

      def test_symlink_blocked_emits_stderr_warning(self, tmp_path, capsys):
          from utils import safe_write_tmp
          link = tmp_path / "zie-test-warn"
          link.symlink_to(tmp_path / "anything")
          safe_write_tmp(link, "x")
          captured = capsys.readouterr()
          assert "WARNING" in captured.err
          assert "symlink" in captured.err.lower()

      def test_oserror_returns_false(self, tmp_path):
          from utils import safe_write_tmp
          from unittest import mock
          target = tmp_path / "zie-test-err"
          with mock.patch("os.replace", side_effect=OSError("disk full")):
              result = safe_write_tmp(target, "data")
          assert result is False

      def test_path_not_exist_is_normal_write(self, tmp_path):
          from utils import safe_write_tmp
          target = tmp_path / "zie-test-new"
          assert not target.exists()
          result = safe_write_tmp(target, "first-run")
          assert result is True
          assert target.read_text() == "first-run"
  ```

  Run: `make test-unit` — must FAIL (`ImportError: cannot import name 'safe_write_tmp'`)

---

- [ ] **Step 2: Implement `safe_write_tmp` in utils.py (GREEN)**

  ```python
  # Append to hooks/utils.py (after project_tmp_path function)

  import os  # add at top of file alongside existing imports

  def safe_write_tmp(path: Path, content: str) -> bool:
      """Atomically write content to path, refusing to follow symlinks.

      Returns True on success, False if path is a symlink or an OSError occurs.
      Uses write-to-.tmp-sibling then os.replace() for atomicity.
      """
      if os.path.islink(path):
          print(
              f"[zie-framework] WARNING: tmp path is a symlink, skipping write: {path}",
              file=sys.stderr,
          )
          return False
      try:
          tmp_path = path.parent / (path.name + ".tmp")
          tmp_path.write_text(content)
          os.replace(tmp_path, path)
          return True
      except OSError:
          return False
  ```

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  No changes to `safe_write_tmp` itself. The `import os` and `import sys` are already
  present at the module level in `utils.py` via the existing `re` and `sys` imports
  — verify `sys` is already imported (it is, line 3) and add `import os` at the top
  alongside the existing imports.

  Run: `make test-unit` — still PASS

---

## Task 2: Wire `safe_write_tmp` into `auto-test.py`

**Acceptance Criteria:**
- The debounce write in `auto-test.py` uses `safe_write_tmp()` instead of direct `write_text` or inline atomic write
- When `safe_write_tmp` returns `False`, the hook continues (treats debounce as cold cache — tests run)

**Files:**
- Modify: `hooks/auto-test.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to class TestAutoTestAtomicDebounceWrite in tests/unit/test_hooks_auto_test.py

  def test_debounce_symlink_does_not_block_hook(self, tmp_path):
      """If debounce path is a symlink, hook skips symlink write and continues."""
      from unittest import mock
      cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
      debounce = project_tmp_path("last-test", cwd.name)
      # Plant a symlink at the debounce path
      real = tmp_path / "real-debounce-target.txt"
      real.write_text("original")
      debounce.symlink_to(real)

      r = run_hook(
          {"tool_name": "Edit", "tool_input": {"file_path": str(cwd / "hooks" / "utils.py")}},
          tmp_cwd=cwd,
      )
      # Hook must not crash
      assert r.returncode == 0
      assert "Traceback" not in r.stderr
      # Original file must be untouched
      assert real.read_text() == "original"
      # Cleanup
      debounce.unlink()
  ```

  Run: `make test-unit` — must FAIL (hook currently calls `write_text` directly, which follows the symlink and overwrites the target)

---

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # In hooks/auto-test.py:

  # 1. Update the import at line 11 to include safe_write_tmp:
  # BEFORE:
  from utils import project_tmp_path
  # AFTER:
  from utils import project_tmp_path, safe_write_tmp

  # 2. Replace the debounce write block (line 87, or the atomic write added by TOCTOU plan):
  # BEFORE (original):
  debounce_file.write_text(file_path)
  # OR BEFORE (if TOCTOU plan was already applied):
  # try:
  #     tmp_write = debounce_file.parent / (debounce_file.name + ".tmp")
  #     tmp_write.write_text(file_path)
  #     os.replace(tmp_write, debounce_file)
  # except OSError:
  #     pass

  # AFTER (either case):
  safe_write_tmp(debounce_file, file_path)
  # No try/except needed — safe_write_tmp handles OSError internally
  ```

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  If the TOCTOU plan was already applied, the inline atomic write block is now replaced
  by the single `safe_write_tmp()` call. Remove the now-redundant `import os` line from
  `auto-test.py` if `os` is no longer used elsewhere in that file. (It is used for
  `os.environ` and `os.path.dirname` — keep the import.)

  Run: `make test-unit` — still PASS

---

## Task 3: Wire `safe_write_tmp` into `wip-checkpoint.py`

**Acceptance Criteria:**
- The counter write in `wip-checkpoint.py` (line 44) uses `safe_write_tmp()` instead of direct `write_text`
- A symlink at the counter path does not overwrite any file the symlink points to

**Files:**
- Modify: `hooks/wip-checkpoint.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  There are no existing dedicated unit tests for `wip-checkpoint.py`. Add a targeted
  integration-style test using subprocess:

  ```python
  # Create tests/unit/test_hooks_wip_checkpoint.py

  """Tests for hooks/wip-checkpoint.py — symlink protection on counter file."""
  import os, sys, json, subprocess
  from pathlib import Path

  REPO_ROOT = Path(__file__).parent.parent.parent
  HOOK = str(REPO_ROOT / "hooks" / "wip-checkpoint.py")
  HOOKS_DIR = str(REPO_ROOT / "hooks")
  sys.path.insert(0, HOOKS_DIR)
  from utils import project_tmp_path


  def run_checkpoint(event, tmp_cwd, env_overrides=None):
      env = {
          **os.environ,
          "CLAUDE_CWD": str(tmp_cwd),
          "ZIE_MEMORY_API_KEY": "test-key",
          "ZIE_MEMORY_API_URL": "https://fake.example.com",
      }
      if env_overrides:
          env.update(env_overrides)
      return subprocess.run(
          [sys.executable, HOOK],
          input=json.dumps(event),
          capture_output=True,
          text=True,
          env=env,
      )


  def make_cwd_with_roadmap(tmp_path):
      zf = tmp_path / "zie-framework"
      zf.mkdir(parents=True)
      (zf / "ROADMAP.md").write_text("## Now\n- [ ] active task\n")
      return tmp_path


  class TestWipCheckpointSymlinkProtection:
      def test_counter_symlink_does_not_overwrite_target(self, tmp_path):
          cwd = make_cwd_with_roadmap(tmp_path)
          counter = project_tmp_path("edit-count", cwd.name)
          real_file = tmp_path / "important.txt"
          real_file.write_text("do not overwrite")
          counter.symlink_to(real_file)

          event = {"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}}
          r = run_checkpoint(event, cwd)

          assert r.returncode == 0
          assert "Traceback" not in r.stderr
          assert real_file.read_text() == "do not overwrite"
          counter.unlink()
  ```

  Run: `make test-unit` — must FAIL (hook calls `counter_file.write_text(str(count))` directly, following the symlink)

---

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # In hooks/wip-checkpoint.py:

  # 1. Update the import at line 10 to include safe_write_tmp:
  # BEFORE:
  from utils import parse_roadmap_now, project_tmp_path
  # AFTER:
  from utils import parse_roadmap_now, project_tmp_path, safe_write_tmp

  # 2. Replace line 44:
  # BEFORE:
  counter_file.write_text(str(count))
  # AFTER:
  safe_write_tmp(counter_file, str(count))
  ```

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  No further changes. The counter-increment logic (`count += 1` before the write) is
  unchanged. If `safe_write_tmp` returns `False` (symlink blocked or OSError), the
  counter value is lost for this invocation — that is the correct behavior per spec
  (counter increment lost, non-fatal).

  Run: `make test-unit` — still PASS

---

**Commit:** `git add hooks/utils.py hooks/auto-test.py hooks/wip-checkpoint.py tests/unit/test_utils.py tests/unit/test_hooks_auto_test.py tests/unit/test_hooks_wip_checkpoint.py && git commit -m "fix: audit-symlink-tmp-attack — safe_write_tmp helper blocks symlink overwrites"`
