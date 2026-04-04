# Silent JSON config parse failures give no user feedback

**Severity**: Medium | **Source**: audit-2026-03-24

## Problem

`auto-test.py:71-74` and `session-resume.py:25-29` catch JSON parse exceptions
on `.config` load and silently continue with defaults. If `.config` is corrupted
(partial write, encoding issue), the hook runs with wrong settings and the user
sees no indication — auto-test may silently skip, session state may be incomplete.

## Motivation

A one-line `print(f"[zie] warning: .config unreadable, using defaults", file=sys.stderr)`
is zero-cost and prevents hours of puzzled debugging when config drifts.
