# Hook Resilience Tests — Error Path + Edge Case Coverage

## Problem

The hook test suite covers happy-path behavior well (1,600+ tests) but has minimal
coverage of error paths and edge cases that could silently break the framework in
production. Key untested scenarios identified:

- `intent-sdlc.py` with uninitialized project (no `zie-framework/` dir) — should
  exit 0 silently, but not tested
- `safety_check_agent.py` when subprocess times out or network is unavailable — should
  fall back to regex-only, not tested
- `subagent-context.py` when `plans/` directory is empty or missing — should inject
  default context, not tested
- `session-resume.py` when `.config` is malformed JSON — should exit 0, not tested
- `auto-test.py` when `make test-unit` hangs beyond wall-clock limit — no timeout test
- Any hook when `zie-framework/` exists but has corrupted/partial state (e.g., empty
  ROADMAP.md, missing PROJECT.md)

## Motivation

Hooks run on every Claude Code event. A hook that crashes or hangs on malformed input
blocks the entire session — one of the hardest failure modes to debug because hooks
run outside Claude's visible context. Test coverage of error paths is the only way
to guarantee the two-tier error handling convention is actually working.

Enterprise deployments hit these edge cases more frequently: CI environments, fresh
clones, partial checkouts, network-restricted environments.

## Rough Scope

New test files (one per hook, edge-case focused):
- `tests/unit/test_hook_uninitialized_project.py` — all hooks exit 0 when no
  `zie-framework/` dir; covers: intent-sdlc, session-resume, auto-test, sdlc-compact,
  safety-check, subagent-context
- `tests/unit/test_hook_malformed_config.py` — all hooks exit 0 with empty / invalid
  JSON in `.config`; covers: load_config(), every hook that calls it
- `tests/unit/test_hook_subprocess_timeout.py` — safety_check_agent falls back to
  regex when subprocess times out; auto-test exits cleanly when make hangs
- `tests/unit/test_hook_partial_state.py` — hooks behave correctly when ROADMAP.md
  is empty, specs/ is missing, plans/ is missing, PROJECT.md is missing
- `tests/unit/test_hook_concurrent_writes.py` — session-cleanup + notification-log
  don't corrupt each other when writing to /tmp simultaneously

Coverage gate: all hooks must have ≥1 error-path test. Add to make test-unit.
