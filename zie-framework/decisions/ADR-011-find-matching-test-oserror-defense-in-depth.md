# ADR-011: find_matching_test() OSError Guards at Every Filesystem Call

Date: 2026-03-24
Status: Accepted

## Context

`find_matching_test()` in `hooks/auto-test.py` uses `tests_dir.rglob()` to
locate test files. The initial OSError fix guarded only the `rglob()` call.
During edge-case testing, `c.exists()` on a candidate path also raised
`PermissionError` when the parent directory was `chmod 000` — the OS resolves
the path against the inaccessible directory and raises before returning a
boolean.

## Decision

OSError guards are applied at **every individual filesystem call** in
`find_matching_test()`, not just at the recursive search entry point:

1. `try/except OSError` around `tests_dir.rglob(...)` — guards the scan itself.
2. `try/except OSError` around `c.exists()` for each candidate — guards
   individual path resolution.

Both silently pass (append nothing / skip the candidate) and allow the function
to return `None` rather than propagating an exception to the hook.

## Consequences

**Positive:** The hook remains crash-proof even when the filesystem is in
pathological states (missing dir, dangling symlinks, permission-denied
subtrees). This matches the hook safety contract: hooks must never raise to
Claude.

**Negative:** A legitimate permission error on a valid test file is silently
ignored rather than surfaced. The hook behaves as if the test file does not
exist — auto-test is skipped for that invocation.

**Neutral:** The pattern generalises: any hook that walks the filesystem should
guard each call individually, not just the walk entry point.
