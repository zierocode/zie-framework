---
approved: true
approved_at: 2026-03-24
backlog: backlog/security-path-traversal.md
---

# Security: Path Traversal Fix in input-sanitizer.py — Design Spec

**Problem:** `hooks/input-sanitizer.py:58` validates that a resolved file path stays within the project root using `str(abs_path).startswith(str(cwd))`. This string prefix check has a known false negative: when `cwd=/home/user` and `abs_path=/home/user-evil/file.txt`, `startswith("/home/user")` returns `True` even though the path is outside the intended directory. Additionally, no tests cover NUL bytes or symlink loops in the input path.

**Approach:** Replace the `startswith()` check with `abs_path.is_relative_to(cwd)` (Python 3.9+, available in Python 3.13 runtime). This method compares path components, not string prefixes, and correctly rejects `/home/user-evil/` when cwd is `/home/user`. Add a `.resolve()` call to `cwd` (already done for `abs_path`) to ensure both sides are fully resolved before comparison. Add three targeted tests covering the edge cases.

**Components:**
- `hooks/input-sanitizer.py`
  - Line 53: `cwd = get_cwd().resolve()` — already resolves, no change needed
  - Line 54: `abs_path = (cwd / p).resolve()` — already resolves, no change needed
  - Line 58: replace `not str(abs_path).startswith(str(cwd))` with `not abs_path.is_relative_to(cwd)`
- `tests/unit/test_input_sanitizer.py`
  - Add `test_path_traversal_user_evil_prefix` — confirms /home/user-evil is rejected
  - Add `test_path_nul_byte_rejected` — confirms NUL byte in path triggers early exit or rejection
  - Add `test_path_with_symlink_outside_cwd` — confirms symlinked path resolving outside cwd is rejected

**Data Flow:**
1. PreToolUse Write/Edit event arrives with `tool_input.file_path`
2. `file_path` is relative (absolute paths exit early at line 51)
3. `cwd = get_cwd().resolve()` — resolves symlinks in cwd
4. `abs_path = (cwd / p).resolve()` — resolves symlinks in path
5. Boundary check:
   - BEFORE: `if not str(abs_path).startswith(str(cwd)):` — false negative for `/home/user-evil/`
   - AFTER: `if not abs_path.is_relative_to(cwd):` — component-wise, correct
6. On rejection: log to stderr, `sys.exit(0)` — hook does NOT block (ADR-003), just skips the path rewrite

**Edge Cases:**
- `/home/user-evil/file.txt` when cwd is `/home/user` → `is_relative_to` correctly returns `False` ✓
- `../../etc/passwd` → resolves to absolute path outside cwd → `is_relative_to` returns `False` ✓
- Valid subdirectory `./src/foo.py` → resolves inside cwd → `is_relative_to` returns `True` ✓
- NUL byte in path (`"foo\x00bar"`) → Python's `Path()` constructor raises `ValueError` on NUL bytes; caught by existing `except Exception` block at line 70 → `sys.exit(0)` ✓. Test verifies hook exits 0, not that the path is "rejected" per se.
- Symlink inside cwd pointing outside cwd → `.resolve()` follows the symlink to its real path, then `is_relative_to` checks the real path against cwd → correctly rejects ✓
- Symlink loop → `Path.resolve()` in Python 3.6+ raises `OSError` (ELOOP) on symlink loops; caught by existing `except Exception` at line 70 → `sys.exit(0)` ✓

**Python version compatibility:**
`Path.is_relative_to()` was added in Python 3.9. The runtime is Python 3.13 (confirmed from bandit output: "running on Python 3.13.7"). No compatibility shim needed.

**Test assertions:**

`test_path_traversal_user_evil_prefix`:
- Set `CLAUDE_CWD=/home/user` (monkeypatched)
- Send Write event with `file_path="../user-evil/evil.py"` (resolves to `/home/user-evil/evil.py`)
- Assert: hook exits 0
- Assert: hook stdout is empty (no `updatedInput` returned — the rewrite is skipped)
- Assert: `"escapes cwd"` appears in hook stderr (existing log message confirms rejection path was taken)

`test_path_nul_byte_rejected`:
- Send Write event with `file_path="foo\x00bar.py"`
- Assert: hook exits 0 (outer guard catches ValueError)
- Assert: hook stdout is empty or valid JSON (no crash)

`test_path_symlink_outside_cwd`:
- Create temp dir with a symlink: `tmpdir/link → /etc`
- Set `CLAUDE_CWD=tmpdir`
- Send Write event with `file_path="link/passwd"`
- Assert: hook exits 0
- Assert: hook stdout is empty (rewrite skipped)

**Out of Scope:**
- Adding a timeout on `Path.resolve()` to guard against symlink loops (Python already raises OSError, which is caught)
- Unicode normalization exploits — Python's `Path` normalizes on construction, no additional handling needed
- Fixing other path comparisons in other hooks — no other hook performs path boundary checks
- Changing the rejection behavior from "skip rewrite" to "block with exit(2)" — hooks are not security boundaries (ADR-003); blocking would be a UX regression
