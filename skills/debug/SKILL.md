---
name: debug
description: Systematic debugging — reproduce, isolate, fix, verify. Uses zie-memory to surface known failure patterns.
metadata:
  zie_memory_enabled: true
user-invocable: false
argument-hint: ""
---

# debug — Systematic Debugging

Reproduce → Isolate → Fix → Verify. No guessing.

## เตรียม context

If `zie_memory_enabled=true`:

- Call `mcp__plugin_zie-memory_zie-memory__recall` with `project=<project> domain=<failing-area> tags=[bug, debug] limit=10`
- Look for: known fragile areas, prior root causes, recurring failure patterns.

## Steps

### ทำซ้ำ bug (Reproduce)

1. Read the full error message + stack trace.
2. Identify the failing test or command.
3. Run the failing test in isolation:

   ```bash
   python3 -m pytest tests/path/test_file.py::TestClass::test_method -v
   ```

4. Confirm: can you reproduce it consistently?
   - Yes → proceed to Phase 2
   - No → intermittent failure, check for timing/ordering issues

### แยกปัญหา (Isolate)

1. Form a hypothesis: "The failure is caused by X because Y."
2. Add a minimal reproduction — reduce to the smallest failing case.
3. Inspect relevant code: read the file, find the function, trace the data flow.
4. Check recent changes: `git log --oneline -10` — did anything change that
   could cause this?

### แก้ bug (Fix)

1. Apply the minimal fix — change only what's needed.
2. Avoid fixing symptoms — address the root cause.
3. Run the failing test: must now PASS.
4. Run the full suite: must still pass.

### ตรวจยืนยัน (Verify)

1. Run full test suite: `make test-unit`
2. If integration tests exist: `make test-int`
3. Confirm no regressions.

### บันทึกการเรียนรู้

If `zie_memory_enabled=true`:

- Call `mcp__plugin_zie-memory_zie-memory__remember`
  with `"Bug: <desc>. Root cause: <why>. Fix: <how>. Pattern: <recurring|one-off>." tags=[bug, <project>, <domain>]`

## กฎที่ต้องทำตาม

- Never comment out a failing test to make the suite pass.
- Never skip the reproduction step — a fix without reproduction is a guess.
- If stuck after 2 attempts → surface the error, explain what you've tried, ask
  for direction.
- If the fix requires a larger refactor → note it as a follow-up, don't
  scope-creep the bugfix.
