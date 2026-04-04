# Fix Release Config Triple Read — Design Spec

**Date:** 2026-04-04  
**Backlog Item:** `zie-framework/backlog/fix-release-config-triple-read.md`

---

## Problem

The `/release` command reads `zie-framework/.config` three times in a single execution:
1. **Pre-flight (Step 2):** Binds `has_frontend` and `playwright_enabled` into scope
2. **Gate 3/5 (line 60):** Reads the file again to check `playwright_enabled`
3. **Gate 4/5 (line 73):** Reads the file again to check both `has_frontend` and `playwright_enabled`

This is redundant: the values are already bound at pre-flight and available in scope.

## Motivation

- **Token cost:** Redundant reads load the same ~20-line JSON file three times unnecessarily
- **Cognitive overhead:** Maintainers tracing the flow see three separate reads instead of one bind + two references, making the command harder to understand
- **Maintainability:** Future changes to config logic require updates in three places instead of one

## Approach

**Single-read binding pattern:** Read and parse `zie-framework/.config` once at pre-flight. Store the result as a variable/context object. Reference the pre-bound values in Gates 3 and 4.

**Rationale:** This is the simplest and clearest pattern — pre-flight already establishes intent to read the file, and Gates 3 and 4 are purely conditional execution based on already-known values. No new logic, no control flow changes, just refactoring the read order.

---

## Components Affected

| File | Change | Reason |
|------|--------|--------|
| `commands/release.md` | Update instructions for Step 2 + Gates 3–4 | Remove redundant reads, reference pre-bound vars |

---

## Design: Step-by-Step

### Pre-flight (Step 2)

**Current:** "อ่าน `zie-framework/.config` — ใช้ has_frontend, playwright_enabled เป็น context"

**Change to:** "Read `zie-framework/.config` into a `config` variable — extract `has_frontend` and `playwright_enabled` for use in Gates 3–4."

In implementation, when the command reads the config file, it stores the parsed JSON object (or extracted fields) in a named variable like `config` so it's referenceable later.

### Gate 3/5 (E2E Tests — Conditional)

**Current:** "Read `playwright_enabled` from `zie-framework/.config` inline."

**Change to:** "Check pre-bound `config.playwright_enabled` (read at pre-flight in Step 2)."

This removes the second read call and references the variable instead.

### Gate 4/5 (Visual Check — Conditional)

**Current:** "Read `has_frontend` and `playwright_enabled` from `zie-framework/.config` inline."

**Change to:** "Check pre-bound `config.has_frontend` and `config.playwright_enabled` (read at pre-flight in Step 2)."

This removes the third read call and references the variables instead.

---

## Data Flow

1. **Pre-flight (Step 2):** Read `zie-framework/.config` once → parse → bind to `config` variable
2. **Gate 3/5:** Reference `config.playwright_enabled` to decide skip/run
3. **Gate 4/5:** Reference `config.has_frontend` and `config.playwright_enabled` to decide skip/run

---

## Edge Cases

- **Config file missing:** Pre-flight already handles this (Step 1 checks `zie-framework/` exists). If the config is absent, the error is caught at Step 2 and the command stops. No change needed.
- **Config invalid JSON:** Handled at pre-flight read time. If parsing fails, error is caught once and reported. Gates 3–4 then reference a valid (or missing) variable safely.

---

## Out of Scope

- No behavior change to when gates execute (skip/run logic unchanged)
- No changes to other commands or hooks
- No changes to config file schema or default values

---

## Acceptance Criteria

1. ✅ `commands/release.md` updated: Step 2 instructions clarified to show binding; Gates 3–4 reference pre-bound variables
2. ✅ Markdown doc reads correctly with no ambiguity about pre-flight binding
3. ✅ `make test-unit` passes (all existing release tests still pass)
4. ✅ Manual test: run `/release` and verify Gates 3 and 4 behavior unchanged (skip/run correctly based on config)

---

## Testing Strategy

**Unit tests** (`zie-framework/tests/test_commands/test_release.py`):
- Existing tests verify gate conditional logic (skip/run based on config)
- All tests should pass after the change (no behavior change, only refactoring)

**Manual verification:**
- Run `/release` on a project with `playwright_enabled=false` → Gate 3 should skip
- Run `/release` on a project with `has_frontend=false` and `playwright_enabled=true` → Gate 4 should skip
- Run `/release` on a project with both `true` → Gates 3 and 4 should run (or fail gracefully if commands missing)

No new tests required (existing test suite already covers conditional skip/run logic).
