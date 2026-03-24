# ADR-010: safe_write_tmp() Hard-Fails on Symlink Detection

Date: 2026-03-24
Status: Accepted

## Context

Hook state files (`/tmp/zie-framework-*/`) are written by multiple hooks.
An attacker (or misconfigured tool) could create a symlink at the expected
path pointing to a sensitive file. A naive `write_text()` call would follow
the symlink and overwrite the target.

## Decision

`safe_write_tmp()` in `hooks/utils.py` checks `path.is_symlink()` before
writing. If a symlink is detected, it logs a `WARNING` to stderr and returns
without writing — it does NOT overwrite through the symlink and does NOT
raise an exception (hooks must never crash).

## Consequences

**Positive:** Symlink attacks on `/tmp` state files are blocked at the utility
level; all hooks that use `safe_write_tmp()` inherit this protection without
per-hook logic.

**Negative:** If a symlink legitimately exists at the state file path (unlikely
but possible), the hook silently skips the write. The counter or debounce file
will not be updated for that invocation.

**Neutral:** Hooks continue to exit 0 on symlink detection — they log a warning
but never block Claude.
