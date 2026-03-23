# ADR-009: Hook __main__ Guard for Direct Unit Testing

Date: 2026-03-23
Status: Accepted

## Context

Hook scripts run as executables (stdin → stdout/exit code) but also contain
helper functions worth unit-testing directly. Without a guard, importing a
hook script in pytest triggers `sys.stdin.read()` at module load, which
hits pytest's stdin capture and causes `SystemExit: 0` before any test runs.

## Decision

Wrap all hook execution code in `if __name__ == "__main__":`. Extract
testable functions (e.g. `find_matching_test`) to module scope with
explicit parameters (no global state). This allows `importlib` to load the
module in tests and call functions directly without subprocess overhead.

## Consequences

__Positive:__ Functions can be unit-tested with direct call semantics;
no subprocess spawn, no stdin mocking required; test isolation is clean.

__Negative:__ Requires discipline — any new logic added to hook scripts
must be placed inside the guard or extracted to a named function, not
written at module scope.

__Neutral:__ Hook execution behavior is unchanged at runtime (scripts are
always invoked as `__main__` by the hook runner).
