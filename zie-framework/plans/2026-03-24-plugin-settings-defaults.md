---
approved: true
approved_at: 2026-03-24
backlog: backlog/plugin-settings-defaults.md
spec: specs/2026-03-24-plugin-settings-defaults-design.md
---

# Plugin settings.json Defaults + CLAUDE_PLUGIN_DATA Storage — Implementation Plan

**Goal:** Ship `.claude-plugin/settings.json` with a valid `agent:` default, add
`get_plugin_data_dir()` / `safe_write_persistent()` / `persistent_project_path()`
to `hooks/utils.py`, and migrate `wip-checkpoint.py` and `session-learn.py` to
write persistent state through those helpers instead of `/tmp` and
`~/.claude/projects/`.

**Architecture:**
- `get_plugin_data_dir(project)` — resolves `$CLAUDE_PLUGIN_DATA` env var;
  falls back to `/tmp/zie-{safe_project}-persistent` with a stderr warning.
- `safe_write_persistent(path, content)` — mirrors `safe_write_tmp()` contract:
  symlink guard + `os.replace()` atomicity. Returns `bool`.
- `persistent_project_path(name, project)` — thin wrapper; mirrors
  `project_tmp_path()`.
- `wip-checkpoint.py` swaps `project_tmp_path` → `persistent_project_path` and
  `safe_write_tmp` → `safe_write_persistent` for the edit-count file only.
- `session-learn.py` replaces manual `~/.claude/projects/<project>/pending_learn.txt`
  construction with `persistent_project_path("pending_learn.txt", project)`.
- `session-resume.py` reads `pending_learn.txt` from the same new path.
- `session-cleanup.py` already globs `/tmp/zie-<project>-*` only — no functional
  change, just a clarifying comment added.

**Tech Stack:** Python 3.x, pytest, stdlib only

**Depends on:** `atomic_write` already present in `utils.py`
(landed in `fix: atomic pending_learn write in session-learn`).

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `.claude-plugin/settings.json` | Plugin-level defaults; `agent:` key |
| Modify | `hooks/utils.py` | Add `get_plugin_data_dir`, `safe_write_persistent`, `persistent_project_path`; module docstring |
| Modify | `hooks/wip-checkpoint.py` | Use `persistent_project_path` + `safe_write_persistent` for edit-count |
| Modify | `hooks/session-learn.py` | Use `persistent_project_path` for pending_learn.txt |
| Modify | `hooks/session-resume.py` | Read pending_learn.txt from persistent path |
| Modify | `hooks/session-cleanup.py` | Add clarifying comment only |
| Modify | `tests/unit/test_utils.py` | New `TestGetPluginDataDir`, `TestSafeWritePersistent`, `TestPersistentProjectPath` classes |
| Modify | `tests/unit/test_hooks_wip_checkpoint.py` | Update counter fixture + assertions to use persistent path |
| Modify | `tests/unit/test_hooks_session_learn.py` | Update pending_learn assertions to use persistent path |

---

## Task 1: Create `.claude-plugin/settings.json`

<!-- depends_on: none -->

**Acceptance Criteria:**
- File exists at `.claude-plugin/settings.json`.
- Valid JSON with `"agent"` key set to empty string.
- `plugin.json` sibling is unchanged.

**Files:**
- Create: `.claude-plugin/settings.json`

**Note:** No test is required for a static JSON file. Validation is a one-time
manual check; CI does not parse `settings.json`. The RED step is a file-existence
assertion run by hand before creating the file.

- [ ] **Step 1: Verify absence (RED)**

  ```bash
  # run from repo root
  test -f .claude-plugin/settings.json && echo EXISTS || echo MISSING
  # Expected output: MISSING
  ```

- [ ] **Step 2: Create file (GREEN)**

  ```json
  {
    "agent": ""
  }
  ```

  Save as `.claude-plugin/settings.json`.

- [ ] **Step 3: Validate (REFACTOR)**

  ```bash
  python3 -c "import json; d=json.load(open('.claude-plugin/settings.json')); assert 'agent' in d; print('ok')"
  # Expected output: ok
  ```

  Confirm `plugin.json` is unmodified (`git diff .claude-plugin/plugin.json` — clean).

---

## Task 2: Add `get_plugin_data_dir()`, `safe_write_persistent()`, and `persistent_project_path()` to `utils.py`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `get_plugin_data_dir(project)` returns a `Path` inside `$CLAUDE_PLUGIN_DATA`
  when the env var is set and non-empty; falls back to
  `/tmp/zie-{safe_project}-persistent` when unset; emits a stderr warning on
  fallback; always calls `mkdir(parents=True, exist_ok=True)` before returning.
- `safe_write_persistent(path, content)` returns `True` on success, `False` when
  target is a symlink (with a stderr WARNING) or when `OSError` is raised. Uses
  `os.replace()` for atomicity. Identical contract to `safe_write_tmp()`.
- `persistent_project_path(name, project)` returns
  `get_plugin_data_dir(project) / name`.
- Module-level docstring added to `utils.py` documenting `/tmp` vs persistent
  storage distinction.
- All existing tests in `test_utils.py` continue to pass.

**Files:**
- Modify: `hooks/utils.py`
- Modify: `tests/unit/test_utils.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add three new test classes to `tests/unit/test_utils.py` after the existing
  `TestSafeWriteTmp` class:

  ```python
  # tests/unit/test_utils.py — add after TestSafeWriteTmp

  class TestGetPluginDataDir:
      def test_uses_claude_plugin_data_when_set(self, tmp_path, monkeypatch):
          from utils import get_plugin_data_dir
          monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
          result = get_plugin_data_dir("my-project")
          assert str(result).startswith(str(tmp_path))

      def test_subdirectory_is_safe_project_name(self, tmp_path, monkeypatch):
          from utils import get_plugin_data_dir, safe_project_name
          monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
          result = get_plugin_data_dir("my project!")
          assert result.name == safe_project_name("my project!")

      def test_directory_is_created(self, tmp_path, monkeypatch):
          from utils import get_plugin_data_dir
          monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
          result = get_plugin_data_dir("newproject")
          assert result.is_dir()

      def test_fallback_to_tmp_when_env_unset(self, monkeypatch, capsys):
          from utils import get_plugin_data_dir, safe_project_name
          monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
          result = get_plugin_data_dir("myproject")
          safe = safe_project_name("myproject")
          assert str(result) == f"/tmp/zie-{safe}-persistent"

      def test_fallback_emits_stderr_warning(self, monkeypatch, capsys):
          from utils import get_plugin_data_dir
          monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
          get_plugin_data_dir("myproject")
          captured = capsys.readouterr()
          assert "CLAUDE_PLUGIN_DATA" in captured.err
          assert "fallback" in captured.err.lower() or "/tmp" in captured.err

      def test_fallback_directory_is_created(self, monkeypatch):
          from utils import get_plugin_data_dir
          monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
          result = get_plugin_data_dir("myproject")
          assert result.is_dir()

      def test_empty_env_var_treated_as_unset(self, monkeypatch, capsys):
          from utils import get_plugin_data_dir
          monkeypatch.setenv("CLAUDE_PLUGIN_DATA", "")
          result = get_plugin_data_dir("myproject")
          assert str(result).startswith("/tmp/")
          captured = capsys.readouterr()
          assert "CLAUDE_PLUGIN_DATA" in captured.err

      def test_returns_path_object(self, tmp_path, monkeypatch):
          from utils import get_plugin_data_dir
          monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
          assert isinstance(get_plugin_data_dir("proj"), Path)

      def test_special_chars_in_project_name_sanitized(self, tmp_path, monkeypatch):
          from utils import get_plugin_data_dir
          monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
          result = get_plugin_data_dir("my/evil/../project")
          # Path() must not escape tmp_path via traversal
          assert str(result).startswith(str(tmp_path))
          assert ".." not in str(result)


  class TestSafeWritePersistent:
      def test_normal_write_returns_true(self, tmp_path):
          from utils import safe_write_persistent
          target = tmp_path / "data.txt"
          result = safe_write_persistent(target, "hello")
          assert result is True
          assert target.read_text() == "hello"

      def test_write_is_atomic_no_tmp_sibling(self, tmp_path):
          from utils import safe_write_persistent
          target = tmp_path / "data.txt"
          safe_write_persistent(target, "content")
          tmp_sibling = tmp_path / "data.txt.tmp"
          assert not tmp_sibling.exists()

      def test_symlink_returns_false(self, tmp_path):
          from utils import safe_write_persistent
          real = tmp_path / "real.txt"
          real.write_text("protected")
          link = tmp_path / "link.txt"
          link.symlink_to(real)
          result = safe_write_persistent(link, "attack")
          assert result is False
          assert real.read_text() == "protected"

      def test_symlink_emits_stderr_warning(self, tmp_path, capsys):
          from utils import safe_write_persistent
          link = tmp_path / "link.txt"
          link.symlink_to(tmp_path / "anything")
          safe_write_persistent(link, "x")
          captured = capsys.readouterr()
          assert "WARNING" in captured.err
          assert "symlink" in captured.err.lower()

      def test_dangling_symlink_returns_false(self, tmp_path):
          from utils import safe_write_persistent
          link = tmp_path / "dangling.txt"
          link.symlink_to(tmp_path / "does-not-exist")
          result = safe_write_persistent(link, "data")
          assert result is False

      def test_oserror_returns_false(self, tmp_path):
          from utils import safe_write_persistent
          from unittest import mock
          target = tmp_path / "err.txt"
          with mock.patch("os.replace", side_effect=OSError("disk full")):
              result = safe_write_persistent(target, "data")
          assert result is False

      def test_overwrites_existing_content(self, tmp_path):
          from utils import safe_write_persistent
          target = tmp_path / "data.txt"
          target.write_text("old")
          safe_write_persistent(target, "new")
          assert target.read_text() == "new"

      def test_path_not_existing_is_normal_write(self, tmp_path):
          from utils import safe_write_persistent
          target = tmp_path / "new.txt"
          assert not target.exists()
          result = safe_write_persistent(target, "first")
          assert result is True
          assert target.read_text() == "first"


  class TestPersistentProjectPath:
      def test_returns_path_inside_plugin_data_dir(self, tmp_path, monkeypatch):
          from utils import persistent_project_path
          monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
          result = persistent_project_path("edit-count", "myproject")
          assert result.parent.parent == tmp_path

      def test_filename_matches_name_arg(self, tmp_path, monkeypatch):
          from utils import persistent_project_path
          monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
          result = persistent_project_path("pending_learn.txt", "myproject")
          assert result.name == "pending_learn.txt"

      def test_returns_path_object(self, tmp_path, monkeypatch):
          from utils import persistent_project_path
          monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
          assert isinstance(persistent_project_path("x", "y"), Path)

      def test_mirrors_project_tmp_path_structure(self, tmp_path, monkeypatch):
          """persistent_project_path and project_tmp_path must use the same
          safe_project_name sanitization for the project segment."""
          from utils import persistent_project_path, safe_project_name
          monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
          result = persistent_project_path("edit-count", "my project!")
          safe = safe_project_name("my project!")
          assert safe in str(result)
  ```

  Run: `make test-unit` — must FAIL (names not yet importable from `utils`).

- [ ] **Step 2: Implement (GREEN)**

  Add to `hooks/utils.py`:

  1. Replace the existing single-line module docstring with:

     ```python
     """Shared utilities for zie-framework hooks. Not a hook — do not run directly.

     Storage tiers
     -------------
     /tmp paths (project_tmp_path / safe_write_tmp):
         Session-scoped state. Cleared by session-cleanup.py on Stop.
         Use for: debounce timestamps, ephemeral counters that reset each session.

     Persistent paths (get_plugin_data_dir / persistent_project_path / safe_write_persistent):
         Cross-session state backed by $CLAUDE_PLUGIN_DATA (set by Claude Code).
         Falls back to /tmp with a warning when the env var is absent.
         Use for: edit counters that survive restart, pending_learn markers.
     """
     ```

  2. Add three functions after `project_tmp_path()`:

     ```python
     def get_plugin_data_dir(project: str) -> Path:
         """Return the persistent data directory for a project.

         Reads $CLAUDE_PLUGIN_DATA (set by Claude Code at hook invocation time).
         If the env var is absent or empty, falls back to a /tmp path and logs a
         warning to stderr so the caller is not silently degraded.

         Always creates the directory before returning.
         """
         base = os.environ.get("CLAUDE_PLUGIN_DATA", "")
         if base:
             path = Path(base) / safe_project_name(project)
         else:
             print(
                 "[zie-framework] CLAUDE_PLUGIN_DATA not set, using /tmp fallback",
                 file=sys.stderr,
             )
             path = Path(f"/tmp/zie-{safe_project_name(project)}-persistent")  # nosec B108
         path.mkdir(parents=True, exist_ok=True)
         return path


     def safe_write_persistent(path: Path, content: str) -> bool:
         """Atomically write content to a persistent path, refusing to follow symlinks.

         Identical contract to safe_write_tmp(): returns True on success, False if
         path is a symlink or an OSError occurs. Uses os.replace() for atomicity.
         """
         if os.path.islink(path):
             print(
                 f"[zie-framework] WARNING: persistent path is a symlink, skipping write: {path}",
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


     def persistent_project_path(name: str, project: str) -> Path:
         """Return a project-scoped persistent path under CLAUDE_PLUGIN_DATA.

         Mirrors project_tmp_path() but uses get_plugin_data_dir() instead of /tmp.
         Example: persistent_project_path("edit-count", "my-proj")
                  -> Path("<CLAUDE_PLUGIN_DATA>/my-proj/edit-count")
         """
         return get_plugin_data_dir(project) / name
     ```

  Run: `make test-unit` — must PASS.

- [ ] **Step 3: Refactor**

  - Confirm all three functions have accurate docstrings.
  - Confirm module docstring clearly distinguishes the two tiers.
  - Confirm no new `import` statements are needed (all dependencies already
    imported: `os`, `sys`, `Path`, `safe_project_name`).
  - Run: `make test-unit` — still PASS.

---

## Task 3: Migrate `wip-checkpoint.py` and `session-learn.py` to persistent storage

<!-- depends_on: Task 2 -->

This task covers three hooks and their tests as one coherent migration.

### 3a: Migrate `wip-checkpoint.py`

**Acceptance Criteria:**
- `wip-checkpoint.py` imports `persistent_project_path` and `safe_write_persistent`
  from `utils`.
- The edit-count file is written to `persistent_project_path("edit-count", cwd.name)`.
- `safe_write_persistent()` is called instead of `safe_write_tmp()`.
- `project_tmp_path` and `safe_write_tmp` are no longer imported in `wip-checkpoint.py`.
- All existing `TestWipCheckpointCounter` and `TestWipCheckpointSymlinkProtection`
  tests pass (updated to use the new path helper).

**Files:**
- Modify: `hooks/wip-checkpoint.py`
- Modify: `tests/unit/test_hooks_wip_checkpoint.py`

- [ ] **Step 1: Write failing tests (RED)**

  In `tests/unit/test_hooks_wip_checkpoint.py`, update the import and all
  counter-path references from `project_tmp_path` to `persistent_project_path`:

  ```python
  # tests/unit/test_hooks_wip_checkpoint.py — update top-level import block

  # Replace:
  #   from utils import project_tmp_path
  # With:
  from utils import persistent_project_path

  # Replace every occurrence of:
  #   project_tmp_path("edit-count", tmp_path.name)
  # With:
  #   persistent_project_path("edit-count", tmp_path.name)
  ```

  Also add a source-inspection test to `TestWipCheckpointUsesProjectTmpPath`:

  ```python
  class TestWipCheckpointUsesProjectTmpPath:
      def test_no_local_counter_path_helper(self):
          """counter_path() local helper must be removed — use project_tmp_path() from utils."""
          src = Path(HOOK).parent.parent / "tests" / "unit" / "test_hooks_wip_checkpoint.py"
          content = src.read_text()
          forbidden = "def " + "counter_path"
          assert forbidden not in content, (
              "counter_path() local helper still present — replace with project_tmp_path() from utils"
          )

      def test_uses_persistent_project_path(self):
          """wip-checkpoint.py must use persistent_project_path for the edit counter."""
          source = Path(HOOK).read_text()
          assert "persistent_project_path" in source, (
              "wip-checkpoint.py must use persistent_project_path, not project_tmp_path"
          )

      def test_does_not_use_project_tmp_path(self):
          """wip-checkpoint.py must not call project_tmp_path for the edit counter."""
          source = Path(HOOK).read_text()
          assert "project_tmp_path" not in source, (
              "wip-checkpoint.py must migrate edit-count to persistent_project_path"
          )
  ```

  Run: `make test-unit` — must FAIL (source assertions fail; counter path
  assertions fail because counter is still written to `/tmp`).

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # hooks/wip-checkpoint.py — update import line:

  # Replace:
  #   from utils import parse_roadmap_now, project_tmp_path, safe_write_tmp, call_zie_memory_api, read_event, get_cwd
  # With:
  from utils import parse_roadmap_now, persistent_project_path, safe_write_persistent, call_zie_memory_api, read_event, get_cwd

  # Replace counter_file assignment (line ~30):
  # Replace:
  #   counter_file = project_tmp_path("edit-count", cwd.name)
  # With:
  counter_file = persistent_project_path("edit-count", cwd.name)

  # Replace safe_write_tmp call (line ~39):
  # Replace:
  #   safe_write_tmp(counter_file, str(count))
  # With:
  safe_write_persistent(counter_file, str(count))
  ```

  Run: `make test-unit` — must PASS.

- [ ] **Step 3: Refactor**

  - Confirm `project_tmp_path` and `safe_write_tmp` do not appear in `wip-checkpoint.py`.
  - Confirm the edit counter now survives across `/tmp` cleans (manual check:
    run hook twice with `CLAUDE_PLUGIN_DATA=/tmp/test-persist`, verify file exists
    at `/tmp/test-persist/<project>/edit-count`).
  - Run: `make test-unit` — still PASS.

---

### 3b: Migrate `session-learn.py`

**Acceptance Criteria:**
- `session-learn.py` imports `persistent_project_path` from `utils`.
- `pending_learn.txt` is written to `persistent_project_path("pending_learn.txt", project)`.
- Manual `Path.home() / ".claude" / "projects" / project` construction is removed.
- `pending_learn_file.parent.mkdir(...)` call is removed (handled by `get_plugin_data_dir`).
- All existing `TestSessionLearnPendingLearnFile` tests pass (updated to use the
  new path helper).

**Files:**
- Modify: `hooks/session-learn.py`
- Modify: `tests/unit/test_hooks_session_learn.py`

- [ ] **Step 1: Write failing tests (RED)**

  In `tests/unit/test_hooks_session_learn.py`, replace the hardcoded pending-learn
  path construction with `persistent_project_path`:

  ```python
  # tests/unit/test_hooks_session_learn.py — add import at top of file

  import sys as _sys
  import os as _os
  _sys.path.insert(0, _os.path.join(REPO_ROOT, "hooks"))
  from utils import persistent_project_path
  ```

  Update `TestSessionLearnPendingLearnFile` — replace all four occurrences of:
  ```python
  pending = Path.home() / ".claude" / "projects" / tmp_path.name / "pending_learn.txt"
  ```
  with:
  ```python
  pending = persistent_project_path("pending_learn.txt", tmp_path.name)
  ```

  Also add a source-inspection test:

  ```python
  class TestSessionLearnUsesPersistentPath:
      def test_uses_persistent_project_path(self):
          """session-learn.py must use persistent_project_path, not hardcoded ~/.claude path."""
          source = Path(HOOK).read_text()
          assert "persistent_project_path" in source, (
              "session-learn.py must use persistent_project_path from utils"
          )

      def test_no_hardcoded_dot_claude_path(self):
          """session-learn.py must not manually construct ~/.claude/projects path."""
          source = Path(HOOK).read_text()
          assert '".claude"' not in source and "'.claude'" not in source, (
              "session-learn.py must not hardcode .claude path — use persistent_project_path"
          )
  ```

  Run: `make test-unit` — must FAIL (path mismatch: file written to old path,
  tests look at new path).

- [ ] **Step 2: Implement (GREEN)**

  Update `session-learn.py` to use `persistent_project_path` from `utils` for
  writing `pending_learn.txt`. Remove manual `~/.claude/projects/` path
  construction.

  Run: `make test-unit` — must PASS.

- [ ] **Step 3: Refactor**

  - Confirm `Path.home()` and `.claude` are absent from `session-learn.py`.
  - Confirm `pending_learn_file.parent.mkdir` call is removed (directory creation
    is handled by `get_plugin_data_dir` inside `persistent_project_path`).
  - Run: `make test-unit` — still PASS.

---

### 3c: Update `session-resume.py` to read from persistent path

**Acceptance Criteria:**
- `session-resume.py` reads `pending_learn.txt` from
  `persistent_project_path("pending_learn.txt", project_name)`.
- If no file is found, resumes without context (existing behavior preserved).
- Hook exits 0 under all conditions.

**Files:**
- Modify: `hooks/session-resume.py`

- [ ] **Step 1 / Step 2 / Step 3**

  Audit `session-resume.py` for `pending_learn` usage. If it reads via the old
  `~/.claude/projects/` path, replace with:
  ```python
  pending_learn_file = persistent_project_path("pending_learn.txt", project_name)
  ```

  Run: `make test-unit` — must PASS.

---

### 3d: Add clarifying comment to `session-cleanup.py`

**Acceptance Criteria:**
- `session-cleanup.py` glob pattern is unchanged (`/tmp/zie-<project>-*`).
- A comment is added making explicit that persistent data is intentionally excluded.

**Files:**
- Modify: `hooks/session-cleanup.py`

- [ ] **Single pass — comment only**

  Add before the glob line:
  ```python
  # Session-scoped /tmp only. Persistent data under $CLAUDE_PLUGIN_DATA is
  # intentionally excluded — it must survive session restart.
  ```

  Run: `make test-unit` — PASS (no test changes needed for a comment).

---

## Commit

```
git add .claude-plugin/settings.json \
        hooks/utils.py \
        hooks/wip-checkpoint.py \
        hooks/session-learn.py \
        hooks/session-resume.py \
        hooks/session-cleanup.py \
        tests/unit/test_utils.py \
        tests/unit/test_hooks_wip_checkpoint.py \
        tests/unit/test_hooks_session_learn.py
git commit -m "feat: settings.json defaults + CLAUDE_PLUGIN_DATA persistent storage"
```
