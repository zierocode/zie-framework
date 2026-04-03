---
slug: audit-safety-check-regex-precompile
status: draft
date: 2026-04-01
---
# Spec: Pre-compile BLOCKS/WARNS Regex Patterns in Safety-Check Hot Path

## Problem

`safety-check.py` calls `re.search(pattern, cmd)` inside a loop on every
`PreToolUse:Bash` invocation — the highest-frequency hook in the plugin.
`utils.BLOCKS` and `utils.WARNS` are lists of `(pattern_str, message)` tuples,
so Python must parse each pattern string on every call. While the `re` module
maintains an internal LRU cache (size 512), cache evictions are possible in
long sessions with diverse commands, and the allocation overhead of the cache
lookup itself is unnecessary when patterns are fixed at startup.

`intent-sdlc.py` already demonstrates the correct fix: module-level
`COMPILED_PATTERNS` built via `re.compile()` at import time. A test in
`tests/unit/test_intent_sdlc_regex.py` enforces this invariant via AST
inspection.

## Proposed Solution

Add `COMPILED_BLOCKS` and `COMPILED_WARNS` constants to `hooks/utils.py`
immediately after the `BLOCKS` and `WARNS` definitions. Each is a list of
`(compiled_pattern, message)` tuples — parallel in structure to the originals
but with `re.compile(pattern)` replacing the raw string.

Update `safety-check.py` to import and use `COMPILED_BLOCKS` / `COMPILED_WARNS`
in the `evaluate()` loop, calling `compiled_pat.search(cmd)` instead of
`re.search(pattern, cmd)`.

Add a test in `tests/unit/test_safety_check_regex.py` that uses the same
AST-inspection pattern as `test_intent_sdlc_regex.py` to assert:

1. `COMPILED_BLOCKS` and `COMPILED_WARNS` are module-level names in `utils.py`.
2. No `re.compile()` call appears inside any function in `utils.py`.
3. `safety-check.py`'s `evaluate()` function does not call `re.search()` with
   a raw string (i.e., the compile step is not deferred into the function).

Compiling in `utils.py` is the single source of truth: any other hook that
imports `BLOCKS`/`WARNS` can also migrate to the compiled variants without
duplicating the compile step.

## Acceptance Criteria

- [ ] AC1: `hooks/utils.py` defines `COMPILED_BLOCKS: list[tuple[re.Pattern, str]]`
      at module level, directly derived from `BLOCKS`.
- [ ] AC2: `hooks/utils.py` defines `COMPILED_WARNS: list[tuple[re.Pattern, str]]`
      at module level, directly derived from `WARNS`.
- [ ] AC3: `hooks/safety-check.py` imports `COMPILED_BLOCKS` and `COMPILED_WARNS`
      from `utils` and uses them in `evaluate()` via `pat.search(cmd)`.
- [ ] AC4: `hooks/safety-check.py` no longer calls `re.search(pattern, cmd)` with
      a raw pattern string inside `evaluate()`.
- [ ] AC5: New test `tests/unit/test_safety_check_regex.py` asserts
      `COMPILED_BLOCKS` and `COMPILED_WARNS` are module-level names in `utils.py`.
- [ ] AC6: New test asserts no `re.compile()` call appears inside any function
      in `utils.py` (compile happens at module level, not lazily).
- [ ] AC7: New test asserts `evaluate()` in `safety-check.py` does not call
      `re.search` with a plain string (enforces use of compiled variants).
- [ ] AC8: Existing `safety-check.py` behavior is unchanged — same commands are
      blocked/warned, same exit codes, same log messages.
- [ ] AC9: `make test-ci` passes with no regressions.

## Out of Scope

- Migrating other hooks (e.g., `safety-check-agent.py`) to use compiled
  patterns — that is a separate item.
- Changing the `BLOCKS`/`WARNS` string-tuple constants themselves; they remain
  for backward compatibility with any code that reads them directly.
- Performance benchmarking or micro-benchmarks — the correctness and
  test-enforcement change is the deliverable.
- Changing the pattern content or adding/removing blocked commands.
