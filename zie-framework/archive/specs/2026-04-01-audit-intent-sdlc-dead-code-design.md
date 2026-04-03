---
slug: audit-intent-sdlc-dead-code
status: draft
date: 2026-04-01
---
# Spec: Remove Dead `__main__` Guard from `intent-sdlc.py`

## Problem

`hooks/intent-sdlc.py` lines 335–336 contain:

```python
if __name__ == "__main__":
    pass
```

All hook logic runs at module top level — the outer guard at line 244 is
module-level code, not inside `__main__`. The `__main__` block does nothing.
This dead code is a remnant of an incomplete refactor and creates a false
expectation that the hook follows the `if __name__ == "__main__"` pattern
used by `auto-test.py` and `task-completed-gate.py`.

## Proposed Solution

**Option A — Remove the dead block (chosen).**

Delete lines 335–336 (`if __name__ == "__main__": pass`) from
`hooks/intent-sdlc.py`. No logic moves, no tests change.

Option B (refactor all module-level logic into `__main__`) is out of scope:
it would require restructuring ~330 lines and adding unit tests for a hook
that currently has none. That is a separate, larger effort.

## Acceptance Criteria

- [ ] AC1: Lines 335–336 (`if __name__ == "__main__": pass`) are deleted from `hooks/intent-sdlc.py`.
- [ ] AC2: No other lines in `intent-sdlc.py` are modified.
- [ ] AC3: `make test-ci` passes with no new failures after the change.
- [ ] AC4: The file still ends with a trailing newline (PEP 8 compliant).

## Out of Scope

- Refactoring hook logic into a `__main__` guard (Option B).
- Adding unit tests for `intent-sdlc.py`.
- Any changes to other hooks or shared utilities.
