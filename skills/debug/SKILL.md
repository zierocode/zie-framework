---
name: zie-framework:debug
description: Systematic debugging — reproduce, isolate, fix, verify. Uses zie-memory to surface known failure patterns.
metadata:
  zie_memory_enabled: true
user-invocable: false
argument-hint: ""
model: sonnet
effort: low
---

# debug — Systematic Debugging

Reproduce → Isolate → Fix → Verify. No guessing.

## เตรียม context

If `zie_memory_enabled=true`:
- Call `mcp__plugin_zie-memory_zie-memory__recall` with `project=<project> domain=<failing-area> tags=[bug, debug] limit=10`
- Look for: known fragile areas, prior root causes, recurring patterns.

## Steps

### ทำซ้ำ bug (Reproduce)

1. Read the full error message + stack trace.
2. Identify the failing test or command.
3. Run it in isolation.
4. Reproducible? → proceed. No → check timing/ordering issues.

### แยกปัญหา (Isolate)

1. Hypothesis: "Failure caused by X because Y."
2. Minimal reproduction — reduce to smallest failing case.
3. Trace the data flow through relevant code.
4. Check recent changes: `git log --oneline -10`.

### แก้ bug (Fix)

1. Apply minimal fix — change only what's needed.
2. Fix root cause, not symptoms.
3. Failing test must now PASS.
4. Full suite must still pass.

### ตรวจยืนยัน (Verify)

1. `make test-unit`
2. If integration tests exist: `make test-int`
3. Confirm no regressions.

### บันทึกการเรียนรู้

If `zie_memory_enabled=true`:
- Call `mcp__plugin_zie-memory_zie-memory__remember` with `"Bug: <desc>. Root cause: <why>. Fix: <how>. Pattern: <recurring|one-off>." tags=[bug, <project>, <domain>]`

## กฎที่ต้องทำตาม

- Never comment out a failing test to make the suite pass.
- Never skip reproduction — a fix without reproduction is a guess.
- Stuck after 2 attempts → surface error, explain what you've tried, ask for direction.
- Fix requires larger refactor → note as follow-up, don't scope-creep the bugfix.