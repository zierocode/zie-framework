# project_tmp_path() untested for pathological inputs

**Severity**: Medium | **Source**: audit-2026-03-24

## Problem

`test_utils.py:54-69` has no tests for: unicode/emoji project names, names with
leading dashes (result: `-proj` → path with leading dash), very long names
(>255 chars, exceeds filename limit on some FSes), or path traversal attempts
(`..` in the project name). All are plausible values for `cwd.name`.

## Motivation

project_tmp_path is the foundation of all /tmp state management. Edge cases here
affect debounce, session state, and cleanup. A long name exceeding the OS filename
limit would cause all hook state writes to silently fail.
