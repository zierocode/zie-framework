---
approved: false
approved_at:
backlog: backlog/security-tmp-hardening.md
spec: specs/2026-03-24-security-tmp-hardening-design.md
---

# Security: /tmp Hardening — Permissions, TOCTOU, Predictable Names — Implementation Plan

**Goal:** Replace predictable `.tmp` sibling filenames and hardcoded `/tmp` strings across `hooks/utils.py` and `hooks/session-cleanup.py` with `tempfile.NamedTemporaryFile` (unpredictable names, atomic creation), `os.chmod(path, 0o600)` (owner-only permissions), and `tempfile.gettempdir()` (portable base path). Resolves three Bandit B108 findings. All function signatures remain unchanged.
**Architecture:** Surgical edits to two hook files only. No new modules. No dependency changes. Tests updated to match the new temp path semantics; four new permission/safety tests added.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/utils.py` | Add `import tempfile`; fix `atomic_write`, `safe_write_tmp`, `safe_write_persistent`, `project_tmp_path`, `get_plugin_data_dir` |
| Modify | `hooks/session-cleanup.py` | Add `import tempfile`; replace `Path("/tmp").glob(...)` |
| Modify | `tests/unit/test_utils.py` | Remove `test_stale_tmp_overwritten`; rewrite `test_no_tmp_file_left_on_success`; fix all hardcoded `/tmp/` path assertions; add 4 new tests |
| Modify | `tests/unit/test_session_cleanup.py` | Fix `test_cleanup_uses_same_rule_as_utils` glob path |

---

## Task 1: Fix `atomic_write` + permissions tests

**Acceptance Criteria:**
- `atomic_write` uses `NamedTemporaryFile(mode='w', dir=path.parent, delete=False, suffix='.tmp')` for the intermediate file
- `os.replace()` moves the temp file to the final path atomically
- `os.chmod(path, 0o600)` is called after `os.replace()` — final file is owner-read/write only
- No predictable `.tmp` sibling is ever created at `path.with_suffix(".tmp")`
- `test_stale_tmp_overwritten` is removed (behavior no longer applicable)
- `test_no_tmp_file_left_on_success` is rewritten as `test_atomic_write_no_predictable_tmp_sibling`
- `test_atomic_write_permissions` asserts `oct(os.stat(path).st_mode)[-3:] == "600"`

**Files:**
- Modify: `hooks/utils.py`
- Modify: `tests/unit/test_utils.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # In tests/unit/test_utils.py — TestAtomicWrite class

  # REMOVE this test entirely:
  # def test_stale_tmp_overwritten(self, tmp_path): ...

  # REWRITE test_no_tmp_file_left_on_success as:
  def test_atomic_write_no_predictable_tmp_sibling(self, tmp_path):
      from utils import atomic_write
      target = tmp_path / "pending_learn.txt"
      atomic_write(target, "hello")
      assert not target.with_suffix(".tmp").exists(), (
          "atomic_write must not leave a predictable .tmp sibling"
      )

  # ADD new test:
  def test_atomic_write_permissions(self, tmp_path):
      from utils import atomic_write
      target = tmp_path / "pending_learn.txt"
      atomic_write(target, "hello")
      mode = oct(os.stat(target).st_mode)[-3:]
      assert mode == "600", f"Expected 600 permissions, got {mode}"
  ```

  Run: `make test-unit` — `test_atomic_write_permissions` must FAIL (current `atomic_write` does not call `os.chmod`)

---

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # hooks/utils.py — add to stdlib imports (alphabetically after 'import os'):
  import tempfile

  # Replace atomic_write (lines 57–65):
  def atomic_write(path: Path, content: str) -> None:
      """Write content to path atomically using an unpredictable temp file and rename.

      Uses tempfile.NamedTemporaryFile to avoid predictable sibling names and
      eliminate the TOCTOU window. Sets owner-only (0o600) permissions on the
      final file after rename.
      """
      with tempfile.NamedTemporaryFile(
          mode='w', dir=path.parent, delete=False, suffix='.tmp'
      ) as f:
          f.write(content)
          tmp_name = f.name
      try:
          os.replace(tmp_name, path)
          os.chmod(path, 0o600)
      except OSError:
          try:
              os.unlink(tmp_name)
          except OSError:
              pass
          raise
  ```

  Run: `make test-unit` — all `TestAtomicWrite` tests must PASS

---

- [ ] **Step 3: Refactor**

  Verify the docstring on line 1 of `utils.py` still references `/tmp` accurately in the Storage tiers section — update the inline comment from "Write-to-.tmp-sibling" to "Write via NamedTemporaryFile" if present.

  Run: `make test-unit` — still PASS
  Run: `make lint-bandit` — B108 count reduced

---

## Task 2: Fix `safe_write_tmp` + `safe_write_persistent`

**Acceptance Criteria:**
- Both functions use `NamedTemporaryFile(mode='w', dir=path.parent, delete=False, suffix='.tmp')` for the intermediate file
- Both call `os.chmod(path, 0o600)` after `os.replace()`
- Both call `os.unlink(tmp_name)` in the `except OSError` block before returning `False`
- No predictable `.tmp` sibling is created
- `test_safe_write_tmp_permissions` asserts mode `600` on `safe_write_tmp` output
- `test_safe_write_persistent_permissions` asserts mode `600` on `safe_write_persistent` output
- Existing `test_write_is_atomic_no_tmp_sibling` and `test_normal_write_is_atomic` pass (sibling gone)

**Files:**
- Modify: `hooks/utils.py`
- Modify: `tests/unit/test_utils.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # In tests/unit/test_utils.py — append to TestSafeWriteTmp class:

  def test_safe_write_tmp_permissions(self, tmp_path):
      from utils import safe_write_tmp
      target = tmp_path / "zie-test-perms"
      safe_write_tmp(target, "data")
      mode = oct(os.stat(target).st_mode)[-3:]
      assert mode == "600", f"Expected 600 permissions, got {mode}"

  # Append to TestSafeWritePersistent class:

  def test_safe_write_persistent_permissions(self, tmp_path):
      from utils import safe_write_persistent
      target = tmp_path / "data.txt"
      safe_write_persistent(target, "data")
      mode = oct(os.stat(target).st_mode)[-3:]
      assert mode == "600", f"Expected 600 permissions, got {mode}"
  ```

  Run: `make test-unit` — both new permission tests must FAIL

---

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # hooks/utils.py — replace safe_write_persistent (lines 107–125):
  def safe_write_persistent(path: Path, content: str) -> bool:
      """Atomically write content to a persistent path, refusing to follow symlinks.

      Uses NamedTemporaryFile for an unpredictable intermediate name. Sets
      owner-only (0o600) permissions on the final file. Returns True on success,
      False if path is a symlink or an OSError occurs.
      """
      if os.path.islink(path):
          print(
              f"[zie-framework] WARNING: persistent path is a symlink, skipping write: {path}",
              file=sys.stderr,
          )
          return False
      try:
          with tempfile.NamedTemporaryFile(
              mode='w', dir=path.parent, delete=False, suffix='.tmp'
          ) as f:
              f.write(content)
              tmp_name = f.name
          os.replace(tmp_name, path)
          os.chmod(path, 0o600)
          return True
      except OSError:
          try:
              os.unlink(tmp_name)
          except OSError:
              pass
          return False

  # hooks/utils.py — replace safe_write_tmp (lines 196–214):
  def safe_write_tmp(path: Path, content: str) -> bool:
      """Atomically write content to path, refusing to follow symlinks.

      Uses NamedTemporaryFile for an unpredictable intermediate name. Sets
      owner-only (0o600) permissions on the final file. Returns True on success,
      False if path is a symlink or an OSError occurs.
      """
      if os.path.islink(path):
          print(
              f"[zie-framework] WARNING: tmp path is a symlink, skipping write: {path}",
              file=sys.stderr,
          )
          return False
      try:
          with tempfile.NamedTemporaryFile(
              mode='w', dir=path.parent, delete=False, suffix='.tmp'
          ) as f:
              f.write(content)
              tmp_name = f.name
          os.replace(tmp_name, path)
          os.chmod(path, 0o600)
          return True
      except OSError:
          try:
              os.unlink(tmp_name)
          except OSError:
              pass
          return False
  ```

  Run: `make test-unit` — all `TestSafeWriteTmp` and `TestSafeWritePersistent` tests must PASS

---

- [ ] **Step 3: Refactor**

  Confirm `test_write_is_atomic_no_tmp_sibling` (line ~268) and `test_normal_write_is_atomic` (line ~361) still pass — they assert that `path.name + ".tmp"` sibling does not exist, which remains true with `NamedTemporaryFile` (the temp name is random, not the old predictable sibling pattern). No changes needed if passing.

  Run: `make test-unit` — still PASS

---

## Task 3: Fix `project_tmp_path` + `get_plugin_data_dir` (Bandit B108)

**Acceptance Criteria:**
- `project_tmp_path` returns `Path(tempfile.gettempdir()) / f"zie-{safe_project_name(project)}-{name}"` — no hardcoded `/tmp`
- `get_plugin_data_dir` fallback returns `Path(tempfile.gettempdir()) / f"zie-{safe_project_name(project)}-persistent"` — no hardcoded `/tmp`
- All `TestProjectTmpPath` and `TestProjectTmpPathEdgeCases` tests updated to use `Path(tempfile.gettempdir())` as the expected base instead of literal `/tmp`
- `test_fallback_to_tmp_when_env_unset` updated to compare against `tempfile.gettempdir()`
- `test_empty_env_var_treated_as_unset` updated: `str(result).startswith(str(tempfile.gettempdir()))` replaces `str(result).startswith("/tmp/")`
- `make lint-bandit` exits 0 (B108 findings in these two functions cleared)

**Files:**
- Modify: `hooks/utils.py`
- Modify: `tests/unit/test_utils.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # In tests/unit/test_utils.py — add import at top of file:
  import tempfile

  # TestProjectTmpPath — rewrite all four tests:
  class TestProjectTmpPath:
      def test_basic_name(self):
          result = project_tmp_path("last-test", "my-project")
          expected = Path(tempfile.gettempdir()) / "zie-my-project-last-test"
          assert result == expected

      def test_spaces_replaced(self):
          result = project_tmp_path("edit-count", "my project!")
          expected = Path(tempfile.gettempdir()) / "zie-my-project--edit-count"
          assert result == expected

      def test_case_preserved(self):
          result = project_tmp_path("x", "ABC")
          expected = Path(tempfile.gettempdir()) / "zie-ABC-x"
          assert result == expected

      def test_returns_path_object(self):
          result = project_tmp_path("foo", "bar")
          assert isinstance(result, Path)

  # TestProjectTmpPathEdgeCases — rewrite all six tests to use tempfile.gettempdir():
  class TestProjectTmpPathEdgeCases:
      def test_unicode_project_name(self):
          result = project_tmp_path("last-test", "mon-projet-caf\u00e9")
          result_str = str(result)
          assert result_str.isascii()
          assert isinstance(result, Path)
          expected = str(Path(tempfile.gettempdir()) / "zie-mon-projet-caf--last-test")
          assert result_str == expected

      def test_emoji_project_name(self):
          result = project_tmp_path("edit-count", "my-app-\U0001F680")
          result_str = str(result)
          assert result_str.isascii()
          assert isinstance(result, Path)
          expected = str(Path(tempfile.gettempdir()) / "zie-my-app---edit-count")
          assert result_str == expected

      def test_leading_dash_project_name(self):
          result = project_tmp_path("last-test", "-myproject")
          expected = str(Path(tempfile.gettempdir()) / "zie--myproject-last-test")
          assert str(result) == expected
          assert isinstance(result, Path)

      def test_very_long_project_name(self):
          long_name = "x" * 256
          result = project_tmp_path("edit-count", long_name)
          assert isinstance(result, Path)
          assert len(result.name) > 255

      def test_path_traversal_attempt(self):
          result = project_tmp_path("last-test", "../etc")
          result_str = str(result)
          assert ".." not in result_str
          parts = Path(result_str).parts
          # First part is the OS temp dir root, not necessarily "/"
          assert "tmp" in result_str.lower() or tempfile.gettempdir() in result_str
          expected = str(Path(tempfile.gettempdir()) / "zie----etc-last-test")
          assert result_str == expected

      def test_dot_only_project_name(self):
          result = project_tmp_path("x", ".")
          result_str = str(result)
          expected = str(Path(tempfile.gettempdir()) / "zie---x")
          assert result_str == expected
          assert isinstance(result, Path)
          assert "/." not in result_str

  # TestGetPluginDataDir — rewrite two tests:
  def test_fallback_to_tmp_when_env_unset(self, monkeypatch, capsys):
      from utils import get_plugin_data_dir, safe_project_name
      monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
      result = get_plugin_data_dir("myproject")
      safe = safe_project_name("myproject")
      expected = Path(tempfile.gettempdir()) / f"zie-{safe}-persistent"
      assert result == expected

  def test_empty_env_var_treated_as_unset(self, monkeypatch, capsys):
      from utils import get_plugin_data_dir
      monkeypatch.setenv("CLAUDE_PLUGIN_DATA", "")
      result = get_plugin_data_dir("myproject")
      assert str(result).startswith(str(tempfile.gettempdir()))
      captured = capsys.readouterr()
      assert "CLAUDE_PLUGIN_DATA" in captured.err
  ```

  Run: `make test-unit` — all updated `TestProjectTmpPath`, `TestProjectTmpPathEdgeCases`, and two `TestGetPluginDataDir` tests must FAIL (still returning `/tmp/...`)

---

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # hooks/utils.py — replace project_tmp_path (line 82):
  def project_tmp_path(name: str, project: str) -> Path:
      """Return a project-scoped tmp path to prevent cross-project collisions.

      Uses tempfile.gettempdir() for portability (resolves Bandit B108).
      Example: project_tmp_path("last-test", "my-project")
               -> Path("/private/tmp/zie-my-project-last-test")  # macOS
               -> Path("/tmp/zie-my-project-last-test")           # Linux
      """
      return Path(tempfile.gettempdir()) / f"zie-{safe_project_name(project)}-{name}"

  # hooks/utils.py — replace fallback in get_plugin_data_dir (line 102):
      path = Path(tempfile.gettempdir()) / f"zie-{safe_project_name(project)}-persistent"
  ```

  Run: `make test-unit` — all updated path tests must PASS
  Run: `make lint-bandit` — B108 findings in `project_tmp_path` and `get_plugin_data_dir` cleared

---

- [ ] **Step 3: Refactor**

  Update the module-level docstring in `utils.py` (lines 1–13): replace the two inline references to `/tmp` in the "Storage tiers" section with `tempfile.gettempdir()` equivalents so the doc stays accurate. Example: `"Falls back to /tmp with a warning"` → `"Falls back to tempfile.gettempdir() with a warning"`.

  Run: `make test-unit` — still PASS

---

## Task 4: Fix `session-cleanup.py`

**Acceptance Criteria:**
- `session-cleanup.py` imports `tempfile`
- `Path("/tmp").glob(...)` on line 17 replaced with `Path(tempfile.gettempdir()).glob(...)`
- Hook still exits 0 on all inputs
- `test_cleanup_uses_same_rule_as_utils` passes on macOS (no longer writes to literal `/tmp`)
- `make lint-bandit` — no B108 finding in `session-cleanup.py`

**Files:**
- Modify: `hooks/session-cleanup.py`
- Modify: `tests/unit/test_session_cleanup.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # In tests/unit/test_session_cleanup.py — rewrite test_cleanup_uses_same_rule_as_utils:

  def test_cleanup_uses_same_rule_as_utils(self):
      """Glob pattern used by session-cleanup must match safe_project_name() output."""
      import tempfile
      sys.path.insert(0, os.path.join(REPO_ROOT, "hooks"))
      from utils import safe_project_name
      project = "my project!"
      safe = safe_project_name(project)
      tmp1 = Path(tempfile.gettempdir()) / f"zie-{safe}-last-test"
      tmp1.write_text("x")
      r = run_hook(project)
      assert r.returncode == 0
      assert not tmp1.exists(), f"{tmp1} should have been deleted"
  ```

  Run: `make test-unit` — `test_cleanup_uses_same_rule_as_utils` must FAIL on macOS (hook still globs `/tmp` which differs from `tempfile.gettempdir()` = `/private/tmp`)

---

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # hooks/session-cleanup.py — add import and replace glob line:

  # Add after 'import os':
  import tempfile

  # Replace line 17:
  # BEFORE:
  for tmp_file in Path("/tmp").glob(f"zie-{safe_project}-*"):
  # AFTER:
  for tmp_file in Path(tempfile.gettempdir()).glob(f"zie-{safe_project}-*"):
  ```

  Run: `make test-unit` — all `TestSessionCleanup*` tests must PASS
  Run: `make lint-bandit` — no B108 findings anywhere in `hooks/`

---

- [ ] **Step 3: Refactor**

  Verify the inline comment on line 15 of `session-cleanup.py` (`# Session-scoped /tmp only`) still reads correctly — update to `# Session-scoped tmp dir only` to reflect portability.

  Run: `make test-unit` — still PASS

---

## Task 5: Full-suite integration check

**Acceptance Criteria:**
- All test changes from Tasks 1–4 are applied and the full test suite is green
- Four new tests exist and pass: `test_safe_write_tmp_permissions`, `test_safe_write_persistent_permissions`, `test_atomic_write_permissions`, `test_atomic_write_no_predictable_tmp_sibling`
- `test_stale_tmp_overwritten` is removed
- No test asserts a hardcoded `/tmp/` prefix for paths that use `project_tmp_path` or `get_plugin_data_dir`
- `make test` (full suite) exits 0

**Files:**
- Modify: `tests/unit/test_utils.py`
- Modify: `tests/unit/test_session_cleanup.py`

---

- [ ] **Step 1: Verify all test changes from Tasks 1–4 are in place**

  Check each item:

  - `test_stale_tmp_overwritten` (line ~101) is deleted from `TestAtomicWrite`
  - `test_no_tmp_file_left_on_success` is replaced by `test_atomic_write_no_predictable_tmp_sibling`
  - `import tempfile` is present at the top of `test_utils.py`
  - `import tempfile` is present in `test_session_cleanup.py` (or inline in the test method)
  - Four new tests exist: `test_atomic_write_permissions`, `test_atomic_write_no_predictable_tmp_sibling`, `test_safe_write_tmp_permissions`, `test_safe_write_persistent_permissions`
  - All `TestProjectTmpPath` and `TestProjectTmpPathEdgeCases` assertions use `Path(tempfile.gettempdir())` not literal `/tmp/`
  - `test_fallback_to_tmp_when_env_unset` and `test_empty_env_var_treated_as_unset` use `tempfile.gettempdir()`
  - `test_cleanup_uses_same_rule_as_utils` writes to `Path(tempfile.gettempdir()) / ...`

  Apply any outstanding fixes, then run: `make test-unit` — must be fully green

---

- [ ] **Step 2: Full suite pass**

  Run the full test suite including integration tests and markdown lint:

  ```bash
  make test
  ```

  All checks must exit 0. If `make lint-bandit` is part of `make test` (wired in via the bandit-sast-ci feature), confirm it passes with zero findings.

---

**Commit:** `git add hooks/utils.py hooks/session-cleanup.py tests/unit/test_utils.py tests/unit/test_session_cleanup.py && git commit -m "fix: security-tmp-hardening — unpredictable tmp names, 0o600 permissions, portable gettempdir"`
