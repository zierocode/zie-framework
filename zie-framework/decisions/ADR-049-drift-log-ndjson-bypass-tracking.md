# ADR-049 — Drift Log NDJSON for SDLC Bypass Tracking

**Status:** Accepted
**Date:** 2026-04-04

## Context

The workflow-enforcement feature required tracking events where users bypass the standard
backlog→spec→plan→implement pipeline (hotfix, spike, chore workflows). We needed a
lightweight, persistent, queryable store that survives process restarts and works without
external dependencies.

## Decision

Implemented `zie-framework/.drift-log` as an NDJSON append-only file with a rolling
200-line window. Each event is a JSON object with `type`, `slug`, `ts`, and `open` fields.
Managed by `hooks/utils_drift.py` with three functions: `append_drift_event`,
`read_drift_count`, and `close_drift_track`.

## Consequences

**Positive:**
- Zero external dependencies; works in any environment
- Trivially queryable: line count = bypass frequency; grep for open entries = active tracks
- Append-only design prevents data loss on partial writes
- Powers retro self-tuning proposals via parse functions in `utils_self_tuning.py`

**Negative:**
- No structured query capability (no SQL, no indexing)
- 200-line rolling window means very old bypass events are lost

**Neutral:**
- File size bounded; no cleanup needed

## Alternatives Considered

- **In-memory counter in hook**: Not persistent across restarts
- **SQLite DB**: Heavier dependency; overkill for event counting
- **JSON file (single object)**: Write conflicts possible under concurrent hook invocations; NDJSON append avoids this
