# Dead __main__ guard in intent-sdlc.py

**Severity**: Low | **Source**: audit-2026-04-01

## Problem

`intent-sdlc.py` lines 335–336 contain `if __name__ == "__main__": pass`.
The entire hook logic executes at module top level — the outer guard at
line 244 is module-level code, not inside `__main__`. The `__main__` block
at the bottom does nothing.

This suggests an incomplete refactor toward the `if __name__ == "__main__"`
pattern used by `auto-test.py` and `task-completed-gate.py`, making the
hook's execution model inconsistent with the rest of the codebase.

## Motivation

Either complete the refactor (move all hook logic into `if __name__ ==
"__main__"`) or remove the dead block. The latter is a one-line fix.
