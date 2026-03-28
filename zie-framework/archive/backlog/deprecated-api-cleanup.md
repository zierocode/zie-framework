# lean: fix deprecated datetime.utcnow() usage

## Problem

`hooks/subagent-stop.py:35` uses `datetime.utcnow()` which is deprecated since
Python 3.12 and emits DeprecationWarning. All other timestamp generation in the
codebase uses `datetime.now(timezone.utc)`.

## Motivation

- **Severity**: Medium (deprecated API, will become error in future Python)
- **Source**: /zie-audit 2026-03-26 finding #20
- Inconsistency with rest of codebase

## Scope

- Replace `datetime.utcnow().isoformat() + "Z"` with
  `datetime.now(timezone.utc).strftime(...)` pattern
- XS effort, auto-fixable
