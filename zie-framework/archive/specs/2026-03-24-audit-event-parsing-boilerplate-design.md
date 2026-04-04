---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-event-parsing-boilerplate.md
---

# Event Parsing Boilerplate Deduplication — Design Spec

**Problem:** Every hook begins with the same `json.loads(sys.stdin.read())` /
`except Exception: sys.exit(0)` block, copied across 7 files; any change to
event parsing must be applied manually to all 7.

**Approach:** Add a `read_event()` helper to `hooks/utils.py` that reads and
parses stdin, exiting cleanly on failure. Each hook replaces its inline block
with a single `event = read_event()` call.

**Components:**

- `hooks/utils.py` — add `read_event()` function
- `hooks/auto-test.py` — replace inline block
- `hooks/intent-detect.py` — replace inline block
- `hooks/safety-check.py` — replace inline block
- `hooks/session-cleanup.py` — replace inline block
- `hooks/session-learn.py` — replace inline block
- `hooks/session-resume.py` — replace inline block
- `hooks/wip-checkpoint.py` — replace inline block

**Data Flow:**

1. Add to `hooks/utils.py`:

   ```python
   def read_event() -> dict:
       """Read and parse the hook event from stdin.

       Exits with code 0 on any parse failure — hooks must never crash.
       """
       try:
           return json.loads(sys.stdin.read())
       except Exception:
           sys.exit(0)
   ```

   Also add `import json` and `import sys` to `utils.py` imports (currently
   only `re` and `sys` are imported; `json` is missing).

2. In each hook file, replace the existing pattern:

   ```python
   try:
       event = json.loads(sys.stdin.read())
   except Exception:
       sys.exit(0)
   ```

   with:

   ```python
   event = read_event()
   ```

   and add `from utils import read_event` (or extend the existing import line).

3. Run `make test-unit` — all existing hook tests must pass unchanged, since
   the behaviour is identical.

**Edge Cases:**

- `safety-check.py` uses `exit(2)` for block signals, not `exit(0)` — the
  `read_event()` helper uses `exit(0)` only for parse failures, which is
  correct; block logic remains in the hook itself
- `auto-test.py` wraps its main logic in `if __name__ == "__main__":` — the
  `read_event()` call moves inside that block; import stays at top level
- `utils.py` is not a standalone hook so `sys.stdin` is never consumed
  at import time; safe to add `import sys` and `import json`

**Out of Scope:**

- Changing exit codes for other failure modes
- Adding event schema validation inside `read_event()`
