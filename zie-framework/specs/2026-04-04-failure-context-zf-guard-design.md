# Design Spec: failure-context — zie-framework Existence Guard

**Slug:** `failure-context-zf-guard`
**Date:** 2026-04-04
**Status:** Approved

## Problem

`failure-context.py` enters inner operations (load_config, ROADMAP read, 2 git
subprocesses) without first checking that `zie-framework/` exists in `cwd`. In
any project without zie-framework initialized, every Bash/Write/Edit failure
triggers unnecessary I/O. All other hooks that touch ROADMAP or git perform
this check first.

## Solution

Add the standard existence guard — `if not (Path(cwd) / "zie-framework").exists(): sys.exit(0)` — immediately after `cwd = get_cwd()`, before `load_config`.

## Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-1 | Hook exits 0 and emits no stdout when `cwd/zie-framework/` does not exist |
| AC-2 | Hook behaves identically to current behavior when `cwd/zie-framework/` exists |
| AC-3 | Guard is placed after outer guard, before `load_config` |
| AC-4 | New test class `TestNoZieFrameworkDir` covers AC-1 with a Bash event |

## Out of Scope

- No changes to config, roadmap parsing, or git caching logic.
