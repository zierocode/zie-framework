# Event parsing boilerplate repeated in all 7 hooks

**Severity**: Low | **Source**: audit-2026-03-24

## Problem

Every hook starts with the same `json.loads(sys.stdin.read())` + `try/except
Exception: sys.exit(0)` pattern. Seven separate copies. Any change to event
parsing logic (e.g., adding validation, changing exit code) must be applied to
all 7 files manually.

## Motivation

A `read_event()` helper in `utils.py` would DRY this to a single call per hook.
Low effort, long-term maintenance win.
