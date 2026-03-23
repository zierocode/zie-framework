# CLAUDE_CWD initialization repeated in 6 hooks

**Severity**: Low | **Source**: audit-2026-03-24

## Problem

`Path(os.environ.get("CLAUDE_CWD", os.getcwd()))` appears identically in 6 hooks:
auto-test, intent-detect, session-cleanup, session-learn, session-resume,
wip-checkpoint. If the env var name or fallback logic changes, all 6 must be
updated.

## Motivation

A `get_cwd()` helper in `utils.py` centralizes this and makes the
CLAUDE_CWD contract visible in one place.
