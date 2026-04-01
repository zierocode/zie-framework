# Pre-compile BLOCKS/WARNS regex patterns in safety-check hot path

**Severity**: Medium | **Source**: audit-2026-04-01

## Problem

`safety-check.py` calls `re.search(pattern, cmd)` inside a loop for every
entry in `utils.BLOCKS` and `utils.WARNS` on every `PreToolUse:Bash` invocation.
Python compiles the pattern fresh on each `re.search()` call (the LRU cache
in the `re` module helps but only for repeated identical strings).

This is a hot-path hook — it fires on every Bash tool call in the session.
`intent-sdlc.py` already demonstrates the correct fix with `COMPILED_PATTERNS`
at module level, and a test in `test_intent_sdlc_regex.py` enforces it.

## Motivation

Pre-compile `BLOCKS` and `WARNS` into a module-level list of compiled patterns
in `utils.py` (alongside the string tuples) or in `safety-check.py` itself.
Apply the same enforcement test pattern used in `test_intent_sdlc_regex.py`.
