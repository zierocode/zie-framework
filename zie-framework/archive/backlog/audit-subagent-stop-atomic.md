# subagent-stop.py bare open() not atomic under concurrent sprint mode

**Severity**: Medium | **Source**: audit-2026-04-01

## Problem

`subagent-stop.py` uses `open(log_path, "a")` to append to the session log.
Under sprint mode, multiple subagents can complete concurrently. Concurrent
`open("a")` across processes is not atomic on all platforms — writes can
interleave, corrupting log entries.

`safe_write_tmp` / `atomic_write` use rename (atomic on POSIX) as the
established pattern in this codebase, but the append path bypasses it.

## Motivation

Implement atomic append: write to a temp file in the same directory and rename
(for replace semantics), or use `fcntl.flock` for true append scenarios. This
mirrors the pattern already applied to other session-scoped log writers.
