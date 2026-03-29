# session-cleanup.py reimplements safe_project sanitization outside utils

**Severity**: Medium | **Source**: audit-2026-03-24

## Problem

`session-cleanup.py:16` contains an inline copy of the sanitization logic from
`utils.project_tmp_path()`: `re.sub(r'[^a-zA-Z0-9]', '-', project)`. If the
sanitization rules change in utils, session-cleanup diverges silently and may
glob the wrong pattern — deleting wrong files or missing leftover state.

## Motivation

Single source of truth. session-cleanup should call `project_tmp_path()` (or a
shared helper) instead of reimplementing the pattern independently.
