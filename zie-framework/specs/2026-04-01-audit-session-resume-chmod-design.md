---
slug: audit-session-resume-chmod
status: approved
date: 2026-04-01
---
# Spec: session-resume.py — chmod 0o600 on CLAUDE_ENV_FILE after write

## Problem

`hooks/session-resume.py` writes environment variables to `CLAUDE_ENV_FILE`
using `Path.write_text()` but does not set file permissions after the write.
Every other write helper in the codebase (`atomic_write`, `safe_write_tmp` in
`hooks/utils.py`) always calls `os.chmod(path, 0o600)` immediately after
writing to ensure owner-only access.

The env file contains project metadata and feature flags
(`ZIE_MEMORY_ENABLED`, `ZIE_PROJECT`, `ZIE_TEST_RUNNER`,
`ZIE_AUTO_TEST_DEBOUNCE_MS`). The sensitivity is low, but the missing chmod
creates a permission hygiene gap: on systems with a permissive umask the file
could be world-readable.

## Proposed Solution

Add `os.chmod(_p, 0o600)` immediately after `_p.write_text(_env_lines)` in
`session-resume.py`, inside the existing `else` branch (after the symlink
guard). No other logic changes.

`import os` is already present at line 4 — no new import needed.

```python
# Before
else:
    _p.write_text(_env_lines)

# After
else:
    _p.write_text(_env_lines)
    os.chmod(_p, 0o600)
```

This matches the pattern used by `atomic_write` (line 186) and
`safe_write_tmp` (line 264 and 513) in `hooks/utils.py`.

## Acceptance Criteria

- [ ] AC1: `os.chmod(_p, 0o600)` is called immediately after `_p.write_text(_env_lines)` in `session-resume.py`
- [ ] AC2: The chmod call is inside the `else` branch — it executes only when the symlink guard passes (not on symlinks)
- [ ] AC3: The chmod call is inside the existing `try/except Exception` block — a chmod failure logs to stderr and does not raise or block Claude
- [ ] AC4: No new `import` statement is required (verified: `import os` already exists at line 4)
- [ ] AC5: The symlink guard logic (`if os.path.islink(_p)`) is unchanged
- [ ] AC6: Existing unit tests for `session-resume.py` continue to pass with no modifications
- [ ] AC7: A unit test asserts that after a successful write the env file has mode `0o600`

## Out of Scope

- Changing the symlink guard logic
- Refactoring the env-file write to use `atomic_write` or `safe_write_tmp`
- Restricting permissions on other files written by hooks not covered by this audit finding
- Changes to `hooks/utils.py`
