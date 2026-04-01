# Cache knowledge-hash result or gate on mtime to avoid rglob on SessionStart

**Severity**: Medium | **Source**: audit-2026-04-01

## Problem

`knowledge-hash.py` `compute_hash()` calls `root.rglob('*')` twice — once to
collect dirs and once inside a list comprehension to count directory contents.
This runs on every `SessionStart` as a subprocess (spawned from
`session-resume.py:81`). No caching, mtime-gating, or short-circuit exists.
The function also iterates every sub-directory with `.iterdir()` for the count
metric — O(dirs × dir_entries) on startup.

## Motivation

Add mtime-gating: compare max mtime of watched paths against cached value; skip
recompute if unchanged. This would reduce most SessionStart overhead to a single
`stat()` call instead of a full recursive walk.
