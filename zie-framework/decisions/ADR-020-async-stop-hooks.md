# ADR-020: Async Stop Hooks for Non-Blocking Session End

Date: 2026-03-25
Status: Accepted

## Context

`session-learn.py` and `session-cleanup.py` run on the `Stop` event and may
involve network calls (zie-memory API) or filesystem operations. Running them
synchronously meant session end could stall if the API was slow or unreachable,
creating a noticeable delay before the next prompt.

## Decision

Both hooks are marked `"async": true` in `hooks.json`. Claude Code spawns them
in the background and does not wait for their exit code. The hooks are
side-effect-only (they never block Claude via exit 2), so async execution is
safe.

## Consequences

**Positive:** Session end is instant regardless of network latency. Hook
failures are silent and do not affect the user experience.
**Negative:** There is no guarantee these hooks complete before the next session
starts. If the API is slow, a memory write may lag by one session.
**Neutral:** `stop-guard.py` remains synchronous because it needs to potentially
block the stop event (exit 2) when uncommitted files are detected.
