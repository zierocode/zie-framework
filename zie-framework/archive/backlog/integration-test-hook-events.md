# Integration Tests — Mock Claude Code Hook Events End-to-End

## Problem

Unit tests mock hook internals but never test the full hook execution path.
A hook that parses the wrong JSON key, crashes on a real event payload, or
exits with the wrong code would not be caught by current unit tests.

## Motivation

Claude Code delivers hook events as JSON via stdin. Testing each hook as a
subprocess with a realistic event payload validates the entire chain: event
parse → logic → stdout/stderr → exit code. This is the only test level that
catches real-world event format bugs.

## Rough Scope

- Create `tests/integration/test_hook_events.py` — one test per hook, runs
  the hook as a subprocess with a realistic event JSON on stdin
- Create `tests/integration/fixtures/` — one sample event JSON per event type
  (SessionStart, PreToolUse, PostToolUse, Stop, etc.)
- Assert on: exit code (always 0), stdout content, stderr content
- Tests run via `pytest tests/integration/` — no live Claude Code process needed
- Out of scope: testing hook behavior with malformed JSON (covered by unit
  tests); testing Claude's response to hook output
