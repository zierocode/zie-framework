# session-resume.py writes CLAUDE_ENV_FILE without 0o600 chmod

**Severity**: Low | **Source**: audit-2026-04-01

## Problem

`session-resume.py` writes the env file using `.write_text()` and does check
for symlinks before writing (correct). However it does not set `0o600`
permissions after writing, unlike every other write helper in the codebase
(`atomic_write`, `safe_write_tmp`) which always call `os.chmod(path, 0o600)`.

The env file contains `ZIE_MEMORY_ENABLED` and project metadata — low
sensitivity, but the inconsistency creates a permission hygiene gap.

## Motivation

Add `os.chmod(env_file_path, 0o600)` after the `write_text()` call in
`session-resume.py` to match the established pattern.
