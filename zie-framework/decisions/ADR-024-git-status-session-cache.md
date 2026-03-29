---
adr: 24
title: Git status session cache for hot-path hooks
status: accepted
date: 2026-03-29
---

# ADR-024 — Git status session cache for hot-path hooks

## Context

`failure-context.py` and `sdlc-compact.py` each spawn git subprocesses
(`git log`, `git branch`, `git diff`) on every invocation. These hooks fire
frequently during active editing sessions — every tool failure and every
pre-compaction event respectively. Each subprocess adds ~50-100ms latency
and OS overhead that compounds on hot paths.

## Decision

Add two helpers to `utils.py`:

- `get_cached_git_status(session_id, key, ttl=5)` — reads from
  `/tmp/zie-<session_id>/git-<key>.cache` if fresh (age < ttl seconds)
- `write_git_status_cache(session_id, key, content)` — writes to the same path

Both hooks consult the cache before spawning a subprocess. Cache miss falls
through to the real subprocess and populates the cache on success.

TTL values chosen per command volatility:
- `branch` / `log` → 5s (changes rarely mid-session)
- `diff` → 2s (changes after every edit, but context window matters more than
  perfect freshness)

`session_id` characters are sanitized with `re.sub(r'[^a-zA-Z0-9_-]', '-', ...)`
before use in path construction to prevent directory traversal.

## Consequences

- Repeated git calls within TTL window hit cache → no subprocess overhead.
- Slightly stale data possible within TTL window — acceptable for context injection.
- Cache files live in `/tmp/zie-<session>/` which is cleaned by `session-cleanup.py` on Stop.
- Pattern is reusable for any future hook that reads slow-changing git state.
