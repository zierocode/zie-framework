# Spec: Merge input-sanitizer into safety-check

**Date:** 2026-04-04
**Status:** Draft
**Feature:** Merge `input-sanitizer.py` into `safety-check.py` to eliminate the double subprocess spawn on every Bash PreToolUse event.

---

## Problem

Every Bash tool call currently spawns **two** sequential hook processes for the `Bash` matcher in `PreToolUse`:

1. `safety-check.py` — blocks destructive commands (regex/agent/both modes)
2. `input-sanitizer.py` — wraps risky-but-legitimate commands in a confirmation prompt

This is wasteful: if `safety-check.py` exits 2 (blocked), the sanitizer still runs (or has already run, depending on ordering). Additionally, the sanitizer evaluating a command that was already blocked creates a confusing execution path. The two hooks share overlapping responsibilities over the same Bash input and should be a single unit.

---

## Proposed Solution

Merge all `input-sanitizer.py` Bash logic into `safety-check.py`. Execute safety-check logic first. If the command is blocked (exit 2), stop immediately — no sanitizer work runs. If the command passes, run sanitizer (confirmation-wrap) logic, then exit 0.

The Write/Edit path from `input-sanitizer.py` (relative path resolution) is **not** part of the Bash matcher but is also absorbed by this merge — it moves into `safety-check.py` as a distinct `Write|Edit` branch. See execution order section below.

---

## Execution Order (within merged hook)

```
PreToolUse:Bash event
        │
        ▼
[1] Safety-check logic (regex / agent / both, per config)
        │
   blocked? ──yes──▶ print BLOCKED message → exit(2)
        │
       no
        ▼
[2] Sanitizer logic (CONFIRM_PATTERNS match + wrap)
        │
   matched + safe? ──yes──▶ emit updatedInput JSON → exit(0)
        │
       no / skipped
        ▼
   exit(0)
```

Write/Edit path (relative path resolution) fires on its own matcher (`Write|Edit`) and is **absorbed by this merge**. This spec mandates Option A: full merge into `safety-check.py`. The Write/Edit path logic moves into `safety-check.py` as a separate branch. `input-sanitizer.py` is deleted after all logic is absorbed.

---

## Changes Required

### `hooks/safety-check.py`
- Absorb all Bash-path logic from `input-sanitizer.py`:
  - `CONFIRM_PATTERNS` list
  - `_DANGEROUS_COMPOUND_RE` regex
  - `_is_safe_for_confirmation_wrapper()` function
  - Confirmation-wrap rewrite logic (emit `updatedInput` JSON)
- Execution order within `__main__`: safety-check evaluate() first → if exit code 2, `sys.exit(2)`; else run sanitizer Bash path → exit(0)
- Write/Edit relative-path-resolution: integrate as a separate `if tool_name in {"Write", "Edit"}` branch before the Bash block

### `hooks/hooks.json`
- Remove the `input-sanitizer.py` entry entirely — no remaining entry for it
- Update the `safety-check.py` matcher in hooks.json from `Bash` to `Write|Edit|Bash` — single entry, unified matcher.

### `hooks/input-sanitizer.py`
- Deleted — all logic absorbed into `safety-check.py`

---

## Test Migration

- Existing `tests/unit/test_input_sanitizer.py` and `tests/unit/test_input_sanitizer_injection.py` cover Bash-path logic (CONFIRM_PATTERNS, wrapper injection, compound guard)
- These tests **must not be deleted** — they move to (or are imported from) `tests/unit/test_hooks_safety_check.py`
- No test coverage may be dropped in the migration
- The merged `test_hooks_safety_check.py` must cover both:
  - All original safety-check blocking/warning assertions
  - All original sanitizer Bash-path assertions (confirm wrap, double-wrap guard, compound skip)
- Write/Edit path tests (relative path resolution) move to a new `test_hooks_safety_check_writeedit.py`

---

## Acceptance Criteria

| # | AC | Verification |
|---|----|----|
| AC-1 | Single subprocess spawned per Bash PreToolUse call (not 2) | `hooks.json` has exactly one entry for safety-check under `PreToolUse[Bash]`; `input-sanitizer.py` entry removed entirely |
| AC-2 | Blocked commands (exit 2) never reach sanitizer logic | Unit test: safety-check blocks → confirm-wrap code path unreachable; add explicit test case |
| AC-3 | All safety-check blocking behaviour preserved | Full `test_hooks_safety_check.py` suite passes with zero regressions |
| AC-4 | All sanitizer metachar-guard behaviour preserved | All `test_input_sanitizer.py` / `test_input_sanitizer_injection.py` Bash-path tests pass under merged file |
| AC-5 | Write/Edit relative-path resolution still works | Existing Write/Edit path tests pass |
| AC-6 | `make test-ci` passes (no new failures, coverage gate met) | CI green |
| AC-7 | `safety_check_agent.py` is unaffected | Its entry in `hooks.json` and tests remain unchanged |
| AC-8 | No test deletion — every test from migrated files survives | `pytest --co -q` shows all test IDs present |

---

## Out of Scope

- Changes to `safety_check_agent.py` (separate subprocess, separate entry in hooks.json)
- Changes to the `mode` config key behaviour (`"regex"` / `"agent"` / `"both"`)
- Any new blocking patterns or sanitizer patterns — this is a structural merge only

---

## Decision Note

The rationale for safety-check first (as stated by the designer):

> If the command is blocked by safety-check (exit 2), there's no point sanitizing it — no wasted work. If it passes safety-check, sanitize/wrap it. Also, safety-check evaluating the **original** command is more predictable than evaluating an already-rewritten wrapper.

This ordering must be preserved exactly in the merged implementation.
