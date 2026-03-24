---
approved: true
approved_at: 2026-03-24
backlog: backlog/security-tmp-hardening.md
---

# Security: /tmp Hardening — Permissions, TOCTOU, Predictable Names — Design Spec

**Problem:** All `/tmp` writes in `hooks/utils.py` use predictable filenames (`path.name + ".tmp"`, `Path(f"/tmp/zie-{project}-{name}")`), default umask permissions (world-readable), and a TOCTOU window between write and rename. Bandit flags three B108 findings. `session-cleanup.py` globs `/tmp` directly, bypassing the symlink-safe utils wrapper.

**Approach:** Four targeted fixes, all within `hooks/utils.py` and `hooks/session-cleanup.py`: (1) replace the predictable `.tmp` intermediate filename in `atomic_write`, `safe_write_tmp`, and `safe_write_persistent` with `tempfile.NamedTemporaryFile(dir=..., delete=False)` — unpredictable name + atomic creation eliminates the TOCTOU window; (2) add `os.chmod(path, 0o600)` after each final `os.replace()` call; (3) replace hardcoded `"/tmp"` string with `tempfile.gettempdir()` in `project_tmp_path()` and `get_plugin_data_dir()` to resolve Bandit B108; (4) migrate `session-cleanup.py:17` from `Path("/tmp").glob(...)` to `Path(tempfile.gettempdir()).glob(...)`. All function signatures remain unchanged.

**Components:**
- `hooks/utils.py`
  - Line 14 area: add `import tempfile` to stdlib import block (after `import os`, alphabetically before `import re`)
  - Lines 57–65 (`atomic_write`): replace `.with_suffix(".tmp")` write with `NamedTemporaryFile` + `os.replace()` + `os.chmod(path, 0o600)`
  - Lines 107–125 (`safe_write_persistent`): same NamedTemporaryFile pattern for intermediate; add `os.chmod(path, 0o600)` after `os.replace()`; add `os.unlink(tmp_name)` in `except OSError` block before `return False`
  - Lines 196–214 (`safe_write_tmp`): same as `safe_write_persistent`
  - Line 82 (`project_tmp_path`): replace `Path(f"/tmp/zie-...")` with `Path(tempfile.gettempdir()) / f"zie-..."`
  - Line 102 (`get_plugin_data_dir`): replace `Path(f"/tmp/zie-...-persistent")` with `Path(tempfile.gettempdir()) / f"zie-...-persistent"`
- `hooks/session-cleanup.py`
  - Line 17: add `import tempfile`; replace `Path("/tmp").glob(...)` with `Path(tempfile.gettempdir()).glob(...)`
- `tests/unit/test_utils.py` — update existing tests + add new tests (see Test section)
- `tests/unit/test_session_cleanup.py` — update glob path assertion

**Data Flow (all three write functions — same pattern):**

BEFORE (`atomic_write` / `safe_write_tmp` / `safe_write_persistent`):
```python
tmp_path = path.with_suffix(".tmp")    # predictable, world-readable
tmp_path.write_text(content)
os.replace(tmp_path, path)             # TOCTOU window
```

AFTER:
```python
import tempfile, os
with tempfile.NamedTemporaryFile(
    mode='w', dir=path.parent, delete=False, suffix='.tmp'
) as f:
    f.write(content)
    tmp_name = f.name                  # unpredictable: /tmp/tmpXXXXXX.tmp
try:
    os.replace(tmp_name, path)
    os.chmod(path, 0o600)             # owner-only permissions
except OSError:
    try:
        os.unlink(tmp_name)            # clean up orphan on failure
    except OSError:
        pass
    return False  # (for safe_write_*; atomic_write re-raises or exits)
```

`project_tmp_path` and `get_plugin_data_dir` base path change:
```python
# BEFORE
Path(f"/tmp/zie-{safe_project_name(project)}-{name}")
# AFTER
Path(tempfile.gettempdir()) / f"zie-{safe_project_name(project)}-{name}"
```

**Edge Cases:**
- `NamedTemporaryFile(delete=False)` — file persists after close; `os.replace()` moves it atomically; on OSError, `os.unlink()` cleans up the orphan.
- `os.chmod(path, 0o600)` — brief window after `os.replace()` where file has default permissions; acceptable on single-user dev machines.
- `tempfile.gettempdir()` — returns `/tmp` on Linux, `/var/folders/.../T/` or `/private/tmp` on macOS. Resolves Bandit B108 by removing the hardcoded literal.
- `atomic_write` callers confirmed via grep: only `session-learn.py:30`. `wip-checkpoint.py`, `stopfailure-log.py`, and `sdlc-compact.py` import from utils but do not call `atomic_write` directly. All callers unaffected — signature unchanged.

**Test changes required (test_utils.py):**

Existing tests to UPDATE (broken by the change):
- `test_stale_tmp_overwritten` (line ~101): currently creates `target.with_suffix(".tmp")` stale file and asserts it's gone after `atomic_write`. After fix, `atomic_write` never touches `.tmp` sibling — the stale file will remain on disk. **Action: remove this test** — the behavior it tested (overwriting a stale `.tmp` sibling) no longer applies; the new behavior (unpredictable temp name) makes the stale file irrelevant.
- `test_no_tmp_file_left_on_success` (line ~82): asserts `target.with_suffix(".tmp")` does not exist after `atomic_write`. After fix this is trivially true (we never create it) but misleading. **Action: rewrite** to assert the temp file directory contains no orphans named `*.tmp` (or simply remove if covered by the NamedTemporaryFile semantics).
- All `TestProjectTmpPath` and `TestProjectTmpPathEdgeCases` tests (lines ~59, 63, 67, 427, 436, 441, 463, 469) hardcode `/tmp/zie-...` as the expected return value. On macOS, `tempfile.gettempdir()` returns `/private/tmp` or `/var/folders/...`, not `/tmp`. **Action: rewrite all** to use `Path(tempfile.gettempdir()) / "zie-..."` as the expected prefix, not the literal string `/tmp/...`.
- `TestGetPluginDataDir.test_fallback_to_tmp_when_env_unset` (line ~222): asserts the fallback path contains `/tmp`. **Action: rewrite** to use `tempfile.gettempdir()` as expected base.

New tests to ADD:
- `test_safe_write_tmp_permissions` — after `safe_write_tmp(path, content)`, assert `oct(os.stat(path).st_mode)[-3:] == "600"`
- `test_safe_write_persistent_permissions` — same for `safe_write_persistent()`
- `test_atomic_write_permissions` — same for `atomic_write()`
- `test_atomic_write_no_predictable_tmp_sibling` — after `atomic_write(path, content)`, assert `path.with_suffix(".tmp")` does not exist (replaces `test_no_tmp_file_left_on_success` semantic)

`tests/unit/test_session_cleanup.py` to UPDATE:
- `test_cleanup_uses_same_rule_as_utils` (line 66): constructs test file at `Path(f"/tmp/zie-{safe}-last-test")` — must change to `Path(tempfile.gettempdir()) / f"zie-{safe}-last-test"` so the hook globs and finds the file after the fix
- Any other test asserting `Path("/tmp")` as the glob base → update to `Path(tempfile.gettempdir())`

`tests/unit/test_utils.py` additional UPDATE:
- `test_empty_env_var_treated_as_unset` (line 242): asserts `str(result).startswith("/tmp/")` — change to `str(result).startswith(str(tempfile.gettempdir()))` to pass on macOS (where gettempdir() returns `/private/tmp` or `/var/folders/...`)

**Out of Scope:**
- Moving session state from `/tmp` to `XDG_RUNTIME_DIR` or project-local `.cache/` — YAGNI
- Encrypting session state files — YAGNI
- Changing the file naming convention `zie-{project}-{name}` — separate concern
- Fixing session-resume.py symlink check — covered in security-path-traversal item
