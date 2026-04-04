# Weak "no-crash" assertions don't verify hook behavior

**Severity**: Medium | **Source**: audit-2026-03-24

## Problem

`test_hooks_wip_checkpoint.py:121,130` (and similar patterns elsewhere) assert
only `returncode == 0`. A hook that exits early with `sys.exit(0)` — doing
nothing — passes these tests. The test provides false confidence that the hook
actually processed the event and produced the expected side-effects.

## Motivation

Tests should assert the observable outcome: file written, stdout content, API
called (mocked). `returncode == 0` is necessary but not sufficient.
